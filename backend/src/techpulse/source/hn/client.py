"""Hacker News API client with resilience and structured logging.

This module provides a production-grade client for the Hacker News Firebase API.
It handles connection pooling, retry logic with exponential backoff, and
structured logging for observability.
"""

import time
from types import TracebackType
from typing import Optional, Self

import httpx
import structlog
from pydantic import ValidationError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from techpulse.source.hn.errors import (
    HackerNewsAPIError,
    HackerNewsDataError,
    HackerNewsMaxRetriesError,
    HackerNewsNetworkError,
)
from techpulse.source.hn.models import HNItem, HNUser

logger = structlog.get_logger(__name__)

DEFAULT_BASE_URL = "https://hacker-news.firebaseio.com/v0"
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 30.0
MAX_RETRY_ATTEMPTS = 5
RATE_LIMIT_DEFAULT_WAIT = 60.0


class HackerNewsClient:
    """Synchronous client for the Hacker News Firebase API.

    This client provides type-safe access to the HN API with automatic retry
    logic for transient failures. It uses connection pooling for efficiency
    and emits structured logs for observability.

    Attributes:
        base_url: The base URL for the HN API.
        connect_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.

    Example:
        >>> with HackerNewsClient() as client:
        ...     item = client.get_item(8863)
        ...     if item and not item.deleted:
        ...         print(item.title)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
    ) -> None:
        """Initialize the Hacker News client.

        Args:
            base_url: Base URL for the HN API. Defaults to official Firebase endpoint.
            connect_timeout: Connection timeout in seconds. Defaults to 10.0.
            read_timeout: Read timeout in seconds. Defaults to 30.0.
        """
        self.base_url = base_url.rstrip("/")
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._client: Optional[httpx.Client] = None
        self._log = logger.bind(component="HackerNewsClient")

    def __enter__(self) -> Self:
        """Enter the context manager and initialize the HTTP client.

        Returns:
            Self: The client instance with an active HTTP session.
        """
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=self.read_timeout,
                pool=self.read_timeout,
            )
        )
        self._log.debug("http_client_initialized")
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit the context manager and close the HTTP client.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._log.debug("http_client_closed")

    def _get_http_client(self) -> httpx.Client:
        """Return the active HTTP client instance.

        Returns:
            httpx.Client: The active HTTP client.

        Raises:
            RuntimeError: If called outside of a context manager.
        """
        if self._client is None:
            raise RuntimeError(
                "HackerNewsClient must be used as a context manager. "
                "Use 'with HackerNewsClient() as client:'"
            )
        return self._client

    def _make_request(self, endpoint: str) -> httpx.Response:
        """Execute an HTTP GET request with retry logic.

        Args:
            endpoint: The API endpoint path (e.g., '/item/8863.json').

        Returns:
            httpx.Response: The successful HTTP response.

        Raises:
            HackerNewsNetworkError: If a network error occurs after all retries.
            HackerNewsAPIError: If the API returns a non-200 status code.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        url = f"{self.base_url}{endpoint}"

        @retry(
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)
            ),
            stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
            wait=wait_exponential_jitter(initial=1, max=30),
            before_sleep=lambda retry_state: self._log.warning(
                "request_retry",
                url=url,
                attempt=retry_state.attempt_number,
                wait_seconds=retry_state.next_action.sleep
                if retry_state.next_action
                else 0,
            ),
        )
        def _execute_request() -> httpx.Response:
            client = self._get_http_client()
            response = client.get(url)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = (
                    float(retry_after) if retry_after else RATE_LIMIT_DEFAULT_WAIT
                )
                self._log.warning(
                    "rate_limited",
                    url=url,
                    retry_after=wait_time,
                )
                time.sleep(wait_time)
                raise httpx.ReadTimeout(f"Rate limited, waited {wait_time}s")

            if response.status_code >= 500:
                self._log.warning(
                    "server_error",
                    url=url,
                    status_code=response.status_code,
                )
                raise httpx.ReadTimeout(f"Server error {response.status_code}")

            if response.status_code != 200:
                raise HackerNewsAPIError(
                    status_code=response.status_code,
                    message=f"Request to {url} failed",
                )

            return response

        try:
            return _execute_request()
        except RetryError as retry_error:
            last_exception = retry_error.last_attempt.exception()
            if last_exception is None:
                raise HackerNewsMaxRetriesError(
                    attempts=MAX_RETRY_ATTEMPTS,
                    last_error=Exception("Unknown error during retry"),
                ) from retry_error
            if isinstance(last_exception, (httpx.ConnectError, httpx.TimeoutException)):
                raise HackerNewsMaxRetriesError(
                    attempts=MAX_RETRY_ATTEMPTS,
                    last_error=last_exception,
                ) from retry_error
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as network_error:
            self._log.error(
                "network_error",
                url=url,
                error=str(network_error),
            )
            raise HackerNewsNetworkError(str(network_error)) from network_error

    def get_item(self, item_id: int) -> Optional[HNItem]:
        """Fetch a single item by ID.

        Args:
            item_id: The unique integer ID of the HN item.

        Returns:
            Optional[HNItem]: The validated item, or None if the item does not exist
                or the API returns null.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsDataError: If response validation fails.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_item_start", item_id=item_id)
        response = self._make_request(f"/item/{item_id}.json")
        data = response.json()

        if data is None:
            self._log.debug("get_item_null", item_id=item_id)
            return None

        try:
            item = HNItem.model_validate(data)
            self._log.debug(
                "get_item_success",
                item_id=item_id,
                item_type=item.type.value,
            )
            return item
        except ValidationError as validation_error:
            self._log.error(
                "get_item_validation_failed",
                item_id=item_id,
                error=str(validation_error),
            )
            raise HackerNewsDataError(
                f"Failed to validate item {item_id}: {validation_error}"
            ) from validation_error

    def get_user(self, username: str) -> Optional[HNUser]:
        """Fetch user metadata by username.

        Args:
            username: The unique username string.

        Returns:
            Optional[HNUser]: The validated user profile, or None if the user
                does not exist.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsDataError: If response validation fails.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_user_start", username=username)
        response = self._make_request(f"/user/{username}.json")
        data = response.json()

        if data is None:
            self._log.debug("get_user_null", username=username)
            return None

        try:
            user = HNUser.model_validate(data)
            self._log.debug(
                "get_user_success",
                username=username,
                karma=user.karma,
            )
            return user
        except ValidationError as validation_error:
            self._log.error(
                "get_user_validation_failed",
                username=username,
                error=str(validation_error),
            )
            raise HackerNewsDataError(
                f"Failed to validate user {username}: {validation_error}"
            ) from validation_error

    def _get_story_ids(self, endpoint: str) -> list[int]:
        """Fetch a list of story IDs from a stories endpoint.

        Args:
            endpoint: The stories endpoint path (e.g., '/topstories.json').

        Returns:
            list[int]: List of story IDs.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        response = self._make_request(endpoint)
        data: list[int] = response.json()
        return data

    def get_top_stories(self) -> list[int]:
        """Fetch current top story IDs.

        Returns:
            list[int]: Up to 500 top story IDs, ordered by rank.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_top_stories_start")
        story_ids = self._get_story_ids("/topstories.json")
        self._log.debug("get_top_stories_success", count=len(story_ids))
        return story_ids

    def get_new_stories(self) -> list[int]:
        """Fetch current new story IDs.

        Returns:
            list[int]: Up to 500 newest story IDs, ordered by recency.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_new_stories_start")
        story_ids = self._get_story_ids("/newstories.json")
        self._log.debug("get_new_stories_success", count=len(story_ids))
        return story_ids

    def get_best_stories(self) -> list[int]:
        """Fetch current best story IDs.

        Returns:
            list[int]: Up to 500 best story IDs, ordered by score.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_best_stories_start")
        story_ids = self._get_story_ids("/beststories.json")
        self._log.debug("get_best_stories_success", count=len(story_ids))
        return story_ids

    def get_ask_stories(self) -> list[int]:
        """Fetch current Ask HN story IDs.

        Returns:
            list[int]: Up to 200 Ask HN story IDs.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_ask_stories_start")
        story_ids = self._get_story_ids("/askstories.json")
        self._log.debug("get_ask_stories_success", count=len(story_ids))
        return story_ids

    def get_show_stories(self) -> list[int]:
        """Fetch current Show HN story IDs.

        Returns:
            list[int]: Up to 200 Show HN story IDs.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_show_stories_start")
        story_ids = self._get_story_ids("/showstories.json")
        self._log.debug("get_show_stories_success", count=len(story_ids))
        return story_ids

    def get_job_stories(self) -> list[int]:
        """Fetch current job story IDs.

        Returns:
            list[int]: Up to 200 job posting IDs.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_job_stories_start")
        story_ids = self._get_story_ids("/jobstories.json")
        self._log.debug("get_job_stories_success", count=len(story_ids))
        return story_ids

    def get_max_item(self) -> int:
        """Fetch the current maximum item ID.

        Returns:
            int: The largest item ID currently in the database.

        Raises:
            HackerNewsNetworkError: If a network error occurs.
            HackerNewsAPIError: If the API returns a non-200 status.
            HackerNewsMaxRetriesError: If all retry attempts are exhausted.
        """
        self._log.debug("get_max_item_start")
        response = self._make_request("/maxitem.json")
        max_item_id: int = response.json()
        self._log.debug("get_max_item_success", max_item_id=max_item_id)
        return max_item_id
