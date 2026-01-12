"""Unit tests for Hacker News Pydantic models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from techpulse.source.hn.models import HNItem, HNItemType, HNUser


class TestHNItemType:
    """Test suite for HNItemType enum."""

    def test_story_value(self) -> None:
        """Verify STORY enum has correct string value."""
        assert HNItemType.STORY.value == "story"

    def test_comment_value(self) -> None:
        """Verify COMMENT enum has correct string value."""
        assert HNItemType.COMMENT.value == "comment"

    def test_job_value(self) -> None:
        """Verify JOB enum has correct string value."""
        assert HNItemType.JOB.value == "job"

    def test_poll_value(self) -> None:
        """Verify POLL enum has correct string value."""
        assert HNItemType.POLL.value == "poll"

    def test_pollopt_value(self) -> None:
        """Verify POLLOPT enum has correct string value."""
        assert HNItemType.POLLOPT.value == "pollopt"

    def test_enum_is_string_subclass(self) -> None:
        """Verify enum values can be used as strings."""
        assert isinstance(HNItemType.STORY, str)
        assert HNItemType.STORY == "story"


class TestHNItem:
    """Test suite for HNItem model."""

    def test_minimal_story_parsing(self) -> None:
        """Verify parsing of minimal story payload."""
        data = {
            "id": 8863,
            "type": "story",
            "by": "dhouston",
            "time": 1175714200,
            "title": "My YC app: Dropbox",
            "url": "http://www.getdropbox.com/u/2/screencast.html",
        }
        item = HNItem.model_validate(data)
        assert item.id == 8863
        assert item.type == HNItemType.STORY
        assert item.by == "dhouston"
        assert item.title == "My YC app: Dropbox"
        assert item.url == "http://www.getdropbox.com/u/2/screencast.html"

    def test_unix_timestamp_conversion(self) -> None:
        """Verify Unix timestamp is converted to UTC datetime."""
        data = {
            "id": 1,
            "type": "story",
            "time": 1175714200,
        }
        item = HNItem.model_validate(data)
        expected_time = datetime.fromtimestamp(1175714200, tz=timezone.utc)
        assert item.time == expected_time
        assert item.time.tzinfo == timezone.utc

    def test_story_with_all_fields(self) -> None:
        """Verify parsing of story with all optional fields populated."""
        data = {
            "id": 8863,
            "type": "story",
            "by": "dhouston",
            "time": 1175714200,
            "title": "My YC app: Dropbox",
            "url": "http://www.getdropbox.com/u/2/screencast.html",
            "score": 111,
            "descendants": 71,
            "kids": [8952, 9224, 8917],
        }
        item = HNItem.model_validate(data)
        assert item.score == 111
        assert item.descendants == 71
        assert item.kids == [8952, 9224, 8917]

    def test_comment_parsing(self) -> None:
        """Verify parsing of comment item."""
        data = {
            "id": 2921983,
            "type": "comment",
            "by": "norvig",
            "time": 1314211127,
            "text": "Aw shucks, guys ...",
            "parent": 2921506,
            "kids": [2922097, 2922429],
        }
        item = HNItem.model_validate(data)
        assert item.type == HNItemType.COMMENT
        assert item.text == "Aw shucks, guys ..."
        assert item.parent == 2921506
        assert item.kids == [2922097, 2922429]

    def test_job_parsing(self) -> None:
        """Verify parsing of job posting."""
        data = {
            "id": 192327,
            "type": "job",
            "by": "justin",
            "time": 1210981217,
            "title": "Justin.tv is looking for engineers",
            "url": "http://www.justin.tv/jobs",
            "score": 6,
        }
        item = HNItem.model_validate(data)
        assert item.type == HNItemType.JOB
        assert item.title == "Justin.tv is looking for engineers"

    def test_poll_parsing(self) -> None:
        """Verify parsing of poll item."""
        data = {
            "id": 126809,
            "type": "poll",
            "by": "pg",
            "time": 1204403652,
            "title": "Poll: What would you pay?",
            "text": "What would you pay per month?",
            "score": 46,
            "descendants": 54,
            "parts": [126810, 126811, 126812],
            "kids": [126822, 126823],
        }
        item = HNItem.model_validate(data)
        assert item.type == HNItemType.POLL
        assert item.parts == [126810, 126811, 126812]

    def test_pollopt_parsing(self) -> None:
        """Verify parsing of poll option."""
        data = {
            "id": 160705,
            "type": "pollopt",
            "by": "pg",
            "time": 1207886576,
            "text": "Yes, ban them",
            "poll": 160704,
            "score": 335,
        }
        item = HNItem.model_validate(data)
        assert item.type == HNItemType.POLLOPT
        assert item.poll == 160704

    def test_deleted_item(self) -> None:
        """Verify parsing of deleted item with flag set."""
        data = {
            "id": 123,
            "type": "comment",
            "time": 1175714200,
            "deleted": True,
        }
        item = HNItem.model_validate(data)
        assert item.deleted is True
        assert item.by is None

    def test_dead_item(self) -> None:
        """Verify parsing of dead/flagged item."""
        data = {
            "id": 456,
            "type": "story",
            "by": "someone",
            "time": 1175714200,
            "title": "Flagged post",
            "dead": True,
        }
        item = HNItem.model_validate(data)
        assert item.dead is True

    def test_default_values(self) -> None:
        """Verify default values for optional fields."""
        data = {
            "id": 1,
            "type": "story",
            "time": 1175714200,
        }
        item = HNItem.model_validate(data)
        assert item.by is None
        assert item.title is None
        assert item.text is None
        assert item.url is None
        assert item.kids == []
        assert item.parent is None
        assert item.score is None
        assert item.descendants is None
        assert item.poll is None
        assert item.parts == []
        assert item.deleted is False
        assert item.dead is False

    def test_missing_required_field_raises_error(self) -> None:
        """Verify validation error when required field is missing."""
        data = {
            "type": "story",
            "time": 1175714200,
        }
        with pytest.raises(ValidationError) as exc_info:
            HNItem.model_validate(data)
        assert "id" in str(exc_info.value)

    def test_invalid_type_raises_error(self) -> None:
        """Verify validation error for invalid item type."""
        data = {
            "id": 1,
            "type": "invalid_type",
            "time": 1175714200,
        }
        with pytest.raises(ValidationError) as exc_info:
            HNItem.model_validate(data)
        assert "type" in str(exc_info.value)

    def test_ignores_unknown_fields(self) -> None:
        """Verify unknown fields are silently ignored for forward compatibility."""
        data = {
            "id": 1,
            "type": "story",
            "time": 1175714200,
            "future_field": "some_value",
            "another_unknown": 123,
        }
        item = HNItem.model_validate(data)
        assert item.id == 1
        assert not hasattr(item, "future_field")


class TestHNUser:
    """Test suite for HNUser model."""

    def test_minimal_user_parsing(self) -> None:
        """Verify parsing of minimal user payload."""
        data = {
            "id": "jl",
            "created": 1173923446,
            "karma": 2937,
        }
        user = HNUser.model_validate(data)
        assert user.id == "jl"
        assert user.karma == 2937

    def test_unix_timestamp_conversion(self) -> None:
        """Verify Unix timestamp is converted to UTC datetime."""
        data = {
            "id": "testuser",
            "created": 1173923446,
            "karma": 100,
        }
        user = HNUser.model_validate(data)
        expected_time = datetime.fromtimestamp(1173923446, tz=timezone.utc)
        assert user.created == expected_time
        assert user.created.tzinfo == timezone.utc

    def test_user_with_all_fields(self) -> None:
        """Verify parsing of user with all fields populated."""
        data = {
            "id": "jl",
            "created": 1173923446,
            "karma": 2937,
            "about": "This is my bio<br>with HTML",
            "submitted": [8265435, 8168423, 8144855],
        }
        user = HNUser.model_validate(data)
        assert user.about == "This is my bio<br>with HTML"
        assert user.submitted == [8265435, 8168423, 8144855]

    def test_default_values(self) -> None:
        """Verify default values for optional fields."""
        data = {
            "id": "newuser",
            "created": 1173923446,
            "karma": 1,
        }
        user = HNUser.model_validate(data)
        assert user.about is None
        assert user.submitted == []

    def test_missing_required_field_raises_error(self) -> None:
        """Verify validation error when required field is missing."""
        data = {
            "id": "testuser",
            "created": 1173923446,
        }
        with pytest.raises(ValidationError) as exc_info:
            HNUser.model_validate(data)
        assert "karma" in str(exc_info.value)

    def test_ignores_unknown_fields(self) -> None:
        """Verify unknown fields are silently ignored for forward compatibility."""
        data = {
            "id": "testuser",
            "created": 1173923446,
            "karma": 100,
            "delay": 0,
            "future_field": "value",
        }
        user = HNUser.model_validate(data)
        assert user.id == "testuser"
        assert not hasattr(user, "delay")
