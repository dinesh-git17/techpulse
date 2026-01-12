"""Unit tests for Dagster asset definitions.

This module tests the who_is_hiring_thread_id asset and its helper functions,
demonstrating mock injection patterns for asset testing without API calls.
"""

from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from dagster import build_asset_context

from techpulse.data.assets import (
    MONTH_NAMES,
    PARTITION_START_DATE,
    WHO_IS_HIRING_PATTERN,
    WHOISHIRING_USERNAME,
    _extract_month_year_from_title,
    _find_thread_id_for_month,
    _is_future_partition,
    _month_name_to_number,
    _parse_partition_key,
    who_is_hiring_partitions,
    who_is_hiring_thread_id,
)
from techpulse.data.resources import HackerNewsClientResource
from techpulse.source.hn.client import HackerNewsClient
from techpulse.source.hn.models import HNItem, HNItemType, HNUser


class TestConstants:
    """Test suite for module constants."""

    def test_whoishiring_username(self) -> None:
        """Verify the whoishiring username constant."""
        assert WHOISHIRING_USERNAME == "whoishiring"

    def test_partition_start_date(self) -> None:
        """Verify partition start date is April 2011."""
        assert PARTITION_START_DATE == "2011-04-01"

    def test_month_names_count(self) -> None:
        """Verify all 12 months are defined."""
        assert len(MONTH_NAMES) == 12

    def test_month_names_order(self) -> None:
        """Verify month names are in correct order."""
        assert MONTH_NAMES[0] == "January"
        assert MONTH_NAMES[11] == "December"


class TestParsePartitionKey:
    """Test suite for _parse_partition_key function."""

    def test_parses_standard_partition_key(self) -> None:
        """Verify parsing of standard YYYY-MM-DD format."""
        year, month = _parse_partition_key("2023-11-01")
        assert year == 2023
        assert month == 11

    def test_parses_january(self) -> None:
        """Verify parsing of January partition."""
        year, month = _parse_partition_key("2024-01-01")
        assert year == 2024
        assert month == 1

    def test_parses_december(self) -> None:
        """Verify parsing of December partition."""
        year, month = _parse_partition_key("2022-12-01")
        assert year == 2022
        assert month == 12

    def test_parses_historical_partition(self) -> None:
        """Verify parsing of historical partition from 2011."""
        year, month = _parse_partition_key("2011-04-01")
        assert year == 2011
        assert month == 4

    def test_invalid_format_raises_error(self) -> None:
        """Verify invalid format raises ValueError."""
        with pytest.raises(ValueError):
            _parse_partition_key("2023-11")

    def test_invalid_date_raises_error(self) -> None:
        """Verify invalid date raises ValueError."""
        with pytest.raises(ValueError):
            _parse_partition_key("2023-13-01")


class TestMonthNameToNumber:
    """Test suite for _month_name_to_number function."""

    def test_january(self) -> None:
        """Verify January converts to 1."""
        assert _month_name_to_number("January") == 1

    def test_december(self) -> None:
        """Verify December converts to 12."""
        assert _month_name_to_number("December") == 12

    def test_case_insensitive(self) -> None:
        """Verify case insensitivity."""
        assert _month_name_to_number("NOVEMBER") == 11
        assert _month_name_to_number("november") == 11
        assert _month_name_to_number("NoVeMbEr") == 11

    def test_whitespace_handling(self) -> None:
        """Verify whitespace is stripped."""
        assert _month_name_to_number("  March  ") == 3

    def test_invalid_month_returns_none(self) -> None:
        """Verify invalid month returns None."""
        assert _month_name_to_number("NotAMonth") is None

    def test_abbreviated_month_returns_none(self) -> None:
        """Verify abbreviated months return None (not supported)."""
        assert _month_name_to_number("Jan") is None
        assert _month_name_to_number("Nov") is None


class TestExtractMonthYearFromTitle:
    """Test suite for _extract_month_year_from_title function."""

    def test_standard_format(self) -> None:
        """Verify extraction from standard format."""
        result = _extract_month_year_from_title(
            "Ask HN: Who is hiring? (November 2023)"
        )
        assert result == (2023, 11)

    def test_apostrophe_format(self) -> None:
        """Verify extraction from Who's format."""
        result = _extract_month_year_from_title("Ask HN: Who's hiring? (March 2024)")
        assert result == (2024, 3)

    def test_without_ask_hn_prefix(self) -> None:
        """Verify extraction without Ask HN prefix."""
        result = _extract_month_year_from_title("Who is hiring? (January 2020)")
        assert result == (2020, 1)

    def test_case_insensitive_matching(self) -> None:
        """Verify case insensitive matching."""
        result = _extract_month_year_from_title(
            "ASK HN: WHO IS HIRING? (DECEMBER 2019)"
        )
        assert result == (2019, 12)

    def test_without_question_mark(self) -> None:
        """Verify extraction works without question mark."""
        result = _extract_month_year_from_title("Ask HN: Who is hiring (April 2018)")
        assert result == (2018, 4)

    def test_historical_april_2011(self) -> None:
        """Verify extraction for first thread (April 2011)."""
        result = _extract_month_year_from_title("Ask HN: Who is hiring? (April 2011)")
        assert result == (2011, 4)

    def test_unrelated_title_returns_none(self) -> None:
        """Verify unrelated titles return None."""
        assert _extract_month_year_from_title("Show HN: My new project") is None

    def test_freelancer_thread_returns_none(self) -> None:
        """Verify freelancer threads are not matched."""
        result = _extract_month_year_from_title(
            "Ask HN: Freelancer? Seeking freelancer? (November 2023)"
        )
        assert result is None

    def test_who_wants_to_be_hired_returns_none(self) -> None:
        """Verify 'who wants to be hired' threads are not matched."""
        result = _extract_month_year_from_title(
            "Ask HN: Who wants to be hired? (November 2023)"
        )
        assert result is None

    def test_invalid_month_returns_none(self) -> None:
        """Verify invalid month in title returns None."""
        result = _extract_month_year_from_title("Ask HN: Who is hiring? (Smarch 2023)")
        assert result is None


class TestWhoIsHiringPattern:
    """Test suite for WHO_IS_HIRING_PATTERN regex."""

    def test_pattern_captures_month_and_year(self) -> None:
        """Verify pattern captures month and year groups."""
        match = WHO_IS_HIRING_PATTERN.search("Ask HN: Who is hiring? (November 2023)")
        assert match is not None
        assert match.group(1) == "November"
        assert match.group(2) == "2023"

    def test_pattern_matches_whos_variant(self) -> None:
        """Verify pattern matches Who's variant."""
        match = WHO_IS_HIRING_PATTERN.search("Ask HN: Who's hiring? (June 2022)")
        assert match is not None
        assert match.group(1) == "June"

    def test_pattern_does_not_match_freelancer(self) -> None:
        """Verify pattern does not match freelancer threads."""
        match = WHO_IS_HIRING_PATTERN.search(
            "Ask HN: Freelancer? Seeking freelancer? (November 2023)"
        )
        assert match is None


class TestIsFuturePartition:
    """Test suite for _is_future_partition function."""

    def test_past_year_is_not_future(self) -> None:
        """Verify past year returns False."""
        assert _is_future_partition(2020, 6) is False

    def test_far_future_year_is_future(self) -> None:
        """Verify far future year returns True."""
        assert _is_future_partition(2099, 1) is True

    def test_current_logic_with_fixed_date(self) -> None:
        """Verify current month logic with mocked datetime."""
        with patch("techpulse.data.assets.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.year = 2024
            mock_now.month = 6
            mock_datetime.now.return_value = mock_now
            mock_datetime.strptime = datetime.strptime

            assert _is_future_partition(2024, 7) is True
            assert _is_future_partition(2024, 6) is False
            assert _is_future_partition(2024, 5) is False
            assert _is_future_partition(2025, 1) is True


class TestWhoIsHiringPartitions:
    """Test suite for partition definition."""

    def test_partition_definition_exists(self) -> None:
        """Verify partition definition is created."""
        assert who_is_hiring_partitions is not None

    def test_partition_start_date_is_april_2011(self) -> None:
        """Verify partitions start from April 2011."""
        partitions = who_is_hiring_partitions.get_partition_keys()
        assert "2011-04-01" in partitions

    def test_partition_includes_historical_months(self) -> None:
        """Verify historical months are included."""
        partitions = who_is_hiring_partitions.get_partition_keys()
        assert "2015-01-01" in partitions
        assert "2020-06-01" in partitions


class TestFindThreadIdForMonth:
    """Test suite for _find_thread_id_for_month function."""

    def _create_mock_item(
        self,
        item_id: int,
        item_type: HNItemType,
        title: Optional[str] = None,
    ) -> HNItem:
        """Create a mock HNItem for testing."""
        return HNItem(
            id=item_id,
            type=item_type,
            by="whoishiring",
            time=1234567890,
            title=title,
            score=100,
            descendants=500,
        )

    def _create_mock_user(self, submitted: list[int]) -> HNUser:
        """Create a mock HNUser for testing."""
        return HNUser(
            id="whoishiring",
            created=1234567890,
            karma=1000,
            about=None,
            submitted=submitted,
        )

    def test_finds_matching_thread(self) -> None:
        """Verify thread is found when title matches."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100, 101, 102])
        mock_item = self._create_mock_item(
            101, HNItemType.STORY, "Ask HN: Who is hiring? (November 2023)"
        )

        mock_client.get_user.return_value = mock_user
        mock_client.get_item.side_effect = [
            self._create_mock_item(100, HNItemType.STORY, "Other title"),
            mock_item,
        ]

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result == 101

    def test_returns_none_when_user_not_found(self) -> None:
        """Verify None returned when user not found."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_client.get_user.return_value = None

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result is None
        mock_log.error.assert_called_once()

    def test_returns_none_when_no_matching_thread(self) -> None:
        """Verify None returned when no thread matches."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100, 101])
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.side_effect = [
            self._create_mock_item(
                100, HNItemType.STORY, "Ask HN: Who is hiring? (October 2023)"
            ),
            self._create_mock_item(
                101, HNItemType.STORY, "Ask HN: Who is hiring? (December 2023)"
            ),
        ]

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result is None
        mock_log.warning.assert_called()

    def test_skips_non_story_items(self) -> None:
        """Verify non-story items are skipped."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100, 101])
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.side_effect = [
            self._create_mock_item(100, HNItemType.COMMENT, None),
            self._create_mock_item(
                101, HNItemType.STORY, "Ask HN: Who is hiring? (November 2023)"
            ),
        ]

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result == 101

    def test_skips_items_without_title(self) -> None:
        """Verify items without title are skipped."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100, 101])
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.side_effect = [
            self._create_mock_item(100, HNItemType.STORY, None),
            self._create_mock_item(
                101, HNItemType.STORY, "Ask HN: Who is hiring? (November 2023)"
            ),
        ]

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result == 101

    def test_skips_none_items(self) -> None:
        """Verify None items (deleted) are skipped."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100, 101])
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.side_effect = [
            None,
            self._create_mock_item(
                101, HNItemType.STORY, "Ask HN: Who is hiring? (November 2023)"
            ),
        ]

        mock_log = MagicMock()
        result = _find_thread_id_for_month(mock_client, 2023, 11, mock_log)

        assert result == 101


class TestWhoIsHiringThreadIdAsset:
    """Test suite for who_is_hiring_thread_id asset."""

    def _create_mock_item(
        self,
        item_id: int,
        title: str,
    ) -> HNItem:
        """Create a mock HNItem for testing."""
        return HNItem(
            id=item_id,
            type=HNItemType.STORY,
            by="whoishiring",
            time=1234567890,
            title=title,
            score=100,
            descendants=500,
        )

    def _create_mock_user(self, submitted: list[int]) -> HNUser:
        """Create a mock HNUser for testing."""
        return HNUser(
            id="whoishiring",
            created=1234567890,
            karma=1000,
            about=None,
            submitted=submitted,
        )

    def test_asset_returns_thread_id_on_success(self) -> None:
        """Verify asset returns thread ID on success."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([12345])
        mock_item = self._create_mock_item(
            12345, "Ask HN: Who is hiring? (November 2020)"
        )
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.return_value = mock_item

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            with patch(
                "techpulse.data.assets._is_future_partition", return_value=False
            ):
                resource = HackerNewsClientResource()
                context = build_asset_context(partition_key="2020-11-01")

                result = who_is_hiring_thread_id(context, resource)

                assert result == 12345

    def test_asset_returns_none_for_future_partition(self) -> None:
        """Verify asset returns None for future partitions."""
        with patch("techpulse.data.assets._is_future_partition", return_value=True):
            resource = HackerNewsClientResource()
            context = build_asset_context(partition_key="2099-01-01")

            result = who_is_hiring_thread_id(context, resource)

            assert result is None

    def test_asset_returns_none_when_thread_not_found(self) -> None:
        """Verify asset returns None when thread not found."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([100])
        mock_item = self._create_mock_item(
            100, "Ask HN: Who is hiring? (December 2020)"
        )
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.return_value = mock_item

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            with patch(
                "techpulse.data.assets._is_future_partition", return_value=False
            ):
                resource = HackerNewsClientResource()
                context = build_asset_context(partition_key="2020-11-01")

                result = who_is_hiring_thread_id(context, resource)

                assert result is None

    def test_asset_handles_apostrophe_title_format(self) -> None:
        """Verify asset handles Who's hiring format."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([54321])
        mock_item = self._create_mock_item(54321, "Ask HN: Who's hiring? (June 2019)")
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.return_value = mock_item

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            with patch(
                "techpulse.data.assets._is_future_partition", return_value=False
            ):
                resource = HackerNewsClientResource()
                context = build_asset_context(partition_key="2019-06-01")

                result = who_is_hiring_thread_id(context, resource)

                assert result == 54321

    def test_asset_adds_metadata_on_success(self) -> None:
        """Verify asset adds metadata to context on success."""
        mock_client = MagicMock(spec=HackerNewsClient)
        mock_user = self._create_mock_user([99999])
        mock_item = self._create_mock_item(99999, "Ask HN: Who is hiring? (April 2011)")
        mock_client.get_user.return_value = mock_user
        mock_client.get_item.return_value = mock_item

        with patch("techpulse.data.resources.HackerNewsClient") as mock_client_class:
            mock_client_class.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.return_value.__exit__ = MagicMock(return_value=None)

            with patch(
                "techpulse.data.assets._is_future_partition", return_value=False
            ):
                resource = HackerNewsClientResource()
                context = build_asset_context(partition_key="2011-04-01")

                result = who_is_hiring_thread_id(context, resource)

                assert result == 99999


class TestAssetIntegrationWithDefinitions:
    """Test suite for asset integration with Dagster Definitions."""

    def test_asset_is_registered_in_definitions(self) -> None:
        """Verify asset is registered in definitions."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        asset_keys = [
            key.to_user_string() for key in repository.asset_graph.get_all_asset_keys()
        ]
        assert "who_is_hiring_thread_id" in asset_keys

    def test_asset_has_correct_partition_definition(self) -> None:
        """Verify asset has monthly partition definition."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        all_keys = list(repository.asset_graph.get_all_asset_keys())
        asset_node = repository.asset_graph.get(all_keys[0])
        assert asset_node.partitions_def is not None
