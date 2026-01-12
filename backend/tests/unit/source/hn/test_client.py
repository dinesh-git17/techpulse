"""Unit tests for Hacker News API client."""

import httpx
import pytest
import respx
from respx import MockRouter

from techpulse.source.hn.client import (
    DEFAULT_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    RATE_LIMIT_DEFAULT_WAIT,
    HackerNewsClient,
    _parse_retry_after,
)
from techpulse.source.hn.errors import (
    HackerNewsAPIError,
    HackerNewsDataError,
    HackerNewsMaxRetriesError,
)
from techpulse.source.hn.models import HNItemType


class TestClientInitialization:
    """Test suite for HackerNewsClient initialization."""

    def test_default_configuration(self) -> None:
        """Verify client initializes with default values."""
        client = HackerNewsClient()
        assert client.base_url == DEFAULT_BASE_URL
        assert client.connect_timeout == DEFAULT_CONNECT_TIMEOUT
        assert client.read_timeout == DEFAULT_READ_TIMEOUT

    def test_custom_configuration(self) -> None:
        """Verify client accepts custom configuration."""
        client = HackerNewsClient(
            base_url="https://custom.api.com/v1",
            connect_timeout=5.0,
            read_timeout=15.0,
        )
        assert client.base_url == "https://custom.api.com/v1"
        assert client.connect_timeout == 5.0
        assert client.read_timeout == 15.0

    def test_base_url_trailing_slash_stripped(self) -> None:
        """Verify trailing slash is removed from base URL."""
        client = HackerNewsClient(base_url="https://api.com/v1/")
        assert client.base_url == "https://api.com/v1"


class TestParseRetryAfter:
    """Test suite for _parse_retry_after helper function."""

    def test_numeric_seconds(self) -> None:
        """Verify numeric string is parsed as seconds."""
        assert _parse_retry_after("120") == 120.0

    def test_numeric_float_seconds(self) -> None:
        """Verify float string is parsed correctly."""
        assert _parse_retry_after("30.5") == 30.5

    def test_none_returns_default(self) -> None:
        """Verify None returns default wait time."""
        assert _parse_retry_after(None) == RATE_LIMIT_DEFAULT_WAIT

    def test_http_date_returns_default(self) -> None:
        """Verify HTTP-date format falls back to default."""
        assert (
            _parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT")
            == RATE_LIMIT_DEFAULT_WAIT
        )

    def test_invalid_string_returns_default(self) -> None:
        """Verify invalid string falls back to default."""
        assert _parse_retry_after("invalid") == RATE_LIMIT_DEFAULT_WAIT

    def test_empty_string_returns_default(self) -> None:
        """Verify empty string falls back to default."""
        assert _parse_retry_after("") == RATE_LIMIT_DEFAULT_WAIT


class TestContextManager:
    """Test suite for context manager protocol."""

    def test_context_manager_initializes_client(self) -> None:
        """Verify HTTP client is created on context entry."""
        with HackerNewsClient() as client:
            assert client._client is not None

    def test_context_manager_closes_client(self) -> None:
        """Verify HTTP client is closed on context exit."""
        client = HackerNewsClient()
        with client:
            pass
        assert client._client is None

    def test_usage_outside_context_raises_error(self) -> None:
        """Verify RuntimeError when methods called outside context."""
        client = HackerNewsClient()
        with pytest.raises(RuntimeError) as exc_info:
            client._get_http_client()
        assert "context manager" in str(exc_info.value)


class TestGetItem:
    """Test suite for get_item method."""

    @respx.mock
    def test_get_item_returns_story(self, respx_mock: MockRouter) -> None:
        """Verify successful story item retrieval."""
        story_data = {
            "id": 8863,
            "type": "story",
            "by": "dhouston",
            "time": 1175714200,
            "title": "My YC app: Dropbox",
            "url": "http://www.getdropbox.com/",
            "score": 111,
            "descendants": 71,
        }
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/8863.json").mock(
            return_value=httpx.Response(200, json=story_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(8863)

        assert item is not None
        assert item.id == 8863
        assert item.type == HNItemType.STORY
        assert item.title == "My YC app: Dropbox"

    @respx.mock
    def test_get_item_returns_none_for_null_response(
        self, respx_mock: MockRouter
    ) -> None:
        """Verify None is returned when API returns null."""
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/999999999.json").mock(
            return_value=httpx.Response(
                200, content=b"null", headers={"content-type": "application/json"}
            )
        )

        with HackerNewsClient() as client:
            item = client.get_item(999999999)

        assert item is None

    @respx.mock
    def test_get_item_handles_deleted_item(self, respx_mock: MockRouter) -> None:
        """Verify deleted items are returned with flag set."""
        deleted_data = {
            "id": 123,
            "type": "comment",
            "time": 1175714200,
            "deleted": True,
        }
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/123.json").mock(
            return_value=httpx.Response(200, json=deleted_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(123)

        assert item is not None
        assert item.deleted is True

    @respx.mock
    def test_get_item_raises_data_error_on_invalid_response(
        self, respx_mock: MockRouter
    ) -> None:
        """Verify HackerNewsDataError raised for invalid data."""
        invalid_data = {
            "id": 123,
            "type": "invalid_type",
            "time": 1175714200,
        }
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/123.json").mock(
            return_value=httpx.Response(200, json=invalid_data)
        )

        with HackerNewsClient() as client:
            with pytest.raises(HackerNewsDataError):
                client.get_item(123)

    @respx.mock
    def test_get_item_raises_api_error_on_404(self, respx_mock: MockRouter) -> None:
        """Verify HackerNewsAPIError raised for 404 response."""
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/123.json").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        with HackerNewsClient() as client:
            with pytest.raises(HackerNewsAPIError) as exc_info:
                client.get_item(123)
        assert exc_info.value.status_code == 404


class TestGetUser:
    """Test suite for get_user method."""

    @respx.mock
    def test_get_user_returns_user(self, respx_mock: MockRouter) -> None:
        """Verify successful user retrieval."""
        user_data = {
            "id": "jl",
            "created": 1173923446,
            "karma": 2937,
            "about": "This is my bio",
            "submitted": [8265435, 8168423],
        }
        respx_mock.get(f"{DEFAULT_BASE_URL}/user/jl.json").mock(
            return_value=httpx.Response(200, json=user_data)
        )

        with HackerNewsClient() as client:
            user = client.get_user("jl")

        assert user is not None
        assert user.id == "jl"
        assert user.karma == 2937

    @respx.mock
    def test_get_user_returns_none_for_nonexistent(
        self, respx_mock: MockRouter
    ) -> None:
        """Verify None is returned for nonexistent user."""
        respx_mock.get(f"{DEFAULT_BASE_URL}/user/nonexistent.json").mock(
            return_value=httpx.Response(
                200, content=b"null", headers={"content-type": "application/json"}
            )
        )

        with HackerNewsClient() as client:
            user = client.get_user("nonexistent")

        assert user is None

    @respx.mock
    def test_get_user_raises_data_error_on_invalid_response(
        self, respx_mock: MockRouter
    ) -> None:
        """Verify HackerNewsDataError raised for invalid user data."""
        invalid_data = {
            "id": "testuser",
            "created": 1173923446,
        }
        respx_mock.get(f"{DEFAULT_BASE_URL}/user/testuser.json").mock(
            return_value=httpx.Response(200, json=invalid_data)
        )

        with HackerNewsClient() as client:
            with pytest.raises(HackerNewsDataError):
                client.get_user("testuser")


class TestStoryEndpoints:
    """Test suite for story list endpoints."""

    @respx.mock
    def test_get_top_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_top_stories returns list of IDs."""
        story_ids = [8863, 8864, 8865]
        respx_mock.get(f"{DEFAULT_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_top_stories()

        assert result == story_ids

    @respx.mock
    def test_get_new_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_new_stories returns list of IDs."""
        story_ids = [9001, 9002, 9003]
        respx_mock.get(f"{DEFAULT_BASE_URL}/newstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_new_stories()

        assert result == story_ids

    @respx.mock
    def test_get_best_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_best_stories returns list of IDs."""
        story_ids = [7001, 7002, 7003]
        respx_mock.get(f"{DEFAULT_BASE_URL}/beststories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_best_stories()

        assert result == story_ids

    @respx.mock
    def test_get_ask_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_ask_stories returns list of IDs."""
        story_ids = [6001, 6002]
        respx_mock.get(f"{DEFAULT_BASE_URL}/askstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_ask_stories()

        assert result == story_ids

    @respx.mock
    def test_get_show_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_show_stories returns list of IDs."""
        story_ids = [5001, 5002]
        respx_mock.get(f"{DEFAULT_BASE_URL}/showstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_show_stories()

        assert result == story_ids

    @respx.mock
    def test_get_job_stories(self, respx_mock: MockRouter) -> None:
        """Verify get_job_stories returns list of IDs."""
        story_ids = [4001, 4002]
        respx_mock.get(f"{DEFAULT_BASE_URL}/jobstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        with HackerNewsClient() as client:
            result = client.get_job_stories()

        assert result == story_ids


class TestGetMaxItem:
    """Test suite for get_max_item method."""

    @respx.mock
    def test_get_max_item_returns_integer(self, respx_mock: MockRouter) -> None:
        """Verify get_max_item returns the maximum item ID."""
        max_id = 42000000
        respx_mock.get(f"{DEFAULT_BASE_URL}/maxitem.json").mock(
            return_value=httpx.Response(200, json=max_id)
        )

        with HackerNewsClient() as client:
            result = client.get_max_item()

        assert result == max_id


class TestRetryBehavior:
    """Test suite for retry and error handling."""

    @respx.mock
    def test_retries_on_server_error(self, respx_mock: MockRouter) -> None:
        """Verify client retries on 5xx errors then succeeds."""
        story_data = {
            "id": 8863,
            "type": "story",
            "by": "dhouston",
            "time": 1175714200,
            "title": "Test",
        }
        route = respx_mock.get(f"{DEFAULT_BASE_URL}/item/8863.json")
        route.side_effect = [
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, json=story_data),
        ]

        with HackerNewsClient() as client:
            item = client.get_item(8863)

        assert item is not None
        assert item.id == 8863
        assert route.call_count == 2

    @respx.mock
    def test_max_retries_exceeded_raises_error(self, respx_mock: MockRouter) -> None:
        """Verify HackerNewsMaxRetriesError after exhausting retries."""
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/8863.json").mock(
            return_value=httpx.Response(503, text="Service Unavailable")
        )

        with HackerNewsClient() as client:
            with pytest.raises(HackerNewsMaxRetriesError) as exc_info:
                client.get_item(8863)
        assert exc_info.value.attempts == 5


class TestErrorHierarchy:
    """Test suite for exception hierarchy."""

    @respx.mock
    def test_api_error_includes_status_code(self, respx_mock: MockRouter) -> None:
        """Verify HackerNewsAPIError contains status code."""
        respx_mock.get(f"{DEFAULT_BASE_URL}/item/123.json").mock(
            return_value=httpx.Response(403, text="Forbidden")
        )

        with HackerNewsClient() as client:
            with pytest.raises(HackerNewsAPIError) as exc_info:
                client.get_item(123)

        assert exc_info.value.status_code == 403
        assert "403" in str(exc_info.value)
