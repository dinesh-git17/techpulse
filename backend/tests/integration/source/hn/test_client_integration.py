"""Integration tests for Hacker News client using recorded cassettes.

These tests validate the client against recorded API responses, ensuring
deterministic behavior in CI while testing the full integration path.
"""

import json
from pathlib import Path
from typing import Iterator

import httpx
import pytest
import respx
from respx import MockRouter

from techpulse.source.hn import (
    HackerNewsClient,
    HNItem,
    HNItemType,
    HNUser,
)
from techpulse.source.hn.client import DEFAULT_BASE_URL

CASSETTES_DIR = Path(__file__).parent / "cassettes"


def load_cassette(filename: str) -> dict[str, object] | list[int] | int | None:
    """Load a cassette JSON file.

    Args:
        filename: The cassette filename (e.g., 'item_8863.json').

    Returns:
        The parsed JSON content.
    """
    cassette_path = CASSETTES_DIR / filename
    with open(cassette_path) as file_handle:
        return json.load(file_handle)  # type: ignore[no-any-return]


@pytest.fixture
def mock_api() -> Iterator[MockRouter]:
    """Create a respx mock router for the HN API."""
    with respx.mock(base_url=DEFAULT_BASE_URL) as mock_router:
        yield mock_router


class TestStoryItemIntegration:
    """Integration tests for story item retrieval."""

    def test_fetch_famous_dropbox_story(self, mock_api: MockRouter) -> None:
        """Validate parsing of the famous Dropbox story (item 8863)."""
        cassette_data = load_cassette("item_8863.json")
        mock_api.get("/item/8863.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(8863)

        assert item is not None
        assert isinstance(item, HNItem)
        assert item.id == 8863
        assert item.type == HNItemType.STORY
        assert item.by == "dhouston"
        assert item.title == "My YC app: Dropbox - Throw away your USB drive"
        assert item.url == "http://www.getdropbox.com/u/2/screencast.html"
        assert item.score == 111
        assert item.descendants == 71
        assert len(item.kids) > 0
        assert item.deleted is False
        assert item.dead is False


class TestCommentItemIntegration:
    """Integration tests for comment item retrieval."""

    def test_fetch_norvig_comment(self, mock_api: MockRouter) -> None:
        """Validate parsing of a comment by norvig."""
        cassette_data = load_cassette("item_2921983.json")
        mock_api.get("/item/2921983.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(2921983)

        assert item is not None
        assert item.type == HNItemType.COMMENT
        assert item.by == "norvig"
        assert item.parent == 2921506
        assert item.text is not None
        assert "Aw shucks" in item.text
        assert len(item.kids) > 0


class TestJobItemIntegration:
    """Integration tests for job posting retrieval."""

    def test_fetch_justin_tv_job(self, mock_api: MockRouter) -> None:
        """Validate parsing of a job posting."""
        cassette_data = load_cassette("item_192327.json")
        mock_api.get("/item/192327.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(192327)

        assert item is not None
        assert item.type == HNItemType.JOB
        assert item.by == "justin"
        assert "Justin.tv" in item.title or ""
        assert item.url is not None


class TestUserIntegration:
    """Integration tests for user profile retrieval."""

    def test_fetch_user_profile(self, mock_api: MockRouter) -> None:
        """Validate parsing of user profile data."""
        cassette_data = load_cassette("user_jl.json")
        mock_api.get("/user/jl.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            user = client.get_user("jl")

        assert user is not None
        assert isinstance(user, HNUser)
        assert user.id == "jl"
        assert user.karma == 2937
        assert user.about is not None
        assert len(user.submitted) > 0
        assert user.created.year > 2000


class TestStoryListsIntegration:
    """Integration tests for story list endpoints."""

    def test_fetch_top_stories(self, mock_api: MockRouter) -> None:
        """Validate top stories endpoint returns list of IDs."""
        cassette_data = load_cassette("topstories.json")
        mock_api.get("/topstories.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            story_ids = client.get_top_stories()

        assert isinstance(story_ids, list)
        assert len(story_ids) > 0
        assert all(isinstance(story_id, int) for story_id in story_ids)


class TestMaxItemIntegration:
    """Integration tests for max item endpoint."""

    def test_fetch_max_item(self, mock_api: MockRouter) -> None:
        """Validate max item endpoint returns integer."""
        cassette_data = load_cassette("maxitem.json")
        mock_api.get("/maxitem.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            max_item_id = client.get_max_item()

        assert isinstance(max_item_id, int)
        assert max_item_id > 0


class TestDeletedItemIntegration:
    """Integration tests for deleted item handling."""

    def test_deleted_item_returns_model_with_flag(self, mock_api: MockRouter) -> None:
        """Verify deleted items are returned with deleted flag set."""
        cassette_data = load_cassette("item_deleted.json")
        mock_api.get("/item/999888.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(999888)

        assert item is not None
        assert item.deleted is True
        assert item.by is None


class TestDeadItemIntegration:
    """Integration tests for dead/flagged item handling."""

    def test_dead_item_returns_model_with_flag(self, mock_api: MockRouter) -> None:
        """Verify dead items are returned with dead flag set."""
        cassette_data = load_cassette("item_dead.json")
        mock_api.get("/item/999777.json").mock(
            return_value=httpx.Response(200, json=cassette_data)
        )

        with HackerNewsClient() as client:
            item = client.get_item(999777)

        assert item is not None
        assert item.dead is True
        assert item.by == "flaggeduser"


class TestNullResponseIntegration:
    """Integration tests for null API responses."""

    def test_null_item_returns_none(self, mock_api: MockRouter) -> None:
        """Verify null response returns None, not an exception."""
        mock_api.get("/item/999999999.json").mock(
            return_value=httpx.Response(
                200, content=b"null", headers={"content-type": "application/json"}
            )
        )

        with HackerNewsClient() as client:
            item = client.get_item(999999999)

        assert item is None

    def test_null_user_returns_none(self, mock_api: MockRouter) -> None:
        """Verify null response for user returns None."""
        mock_api.get("/user/nonexistent_user_12345.json").mock(
            return_value=httpx.Response(
                200, content=b"null", headers={"content-type": "application/json"}
            )
        )

        with HackerNewsClient() as client:
            user = client.get_user("nonexistent_user_12345")

        assert user is None
