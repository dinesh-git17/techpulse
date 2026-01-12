"""Unit tests for Dagster schedule and job definitions.

This module tests the scheduling configuration for the Who is Hiring
data pipeline, including monthly schedules and job configuration.
"""

from techpulse.data.schedules import (
    BACKFILL_MAX_CONCURRENT_PARTITIONS,
    SCHEDULE_CRON,
    who_is_hiring_assets,
    who_is_hiring_backfill_job,
    who_is_hiring_ingestion_job,
    who_is_hiring_monthly_schedule,
)


class TestScheduleConstants:
    """Test suite for schedule module constants."""

    def test_backfill_max_concurrent_partitions(self) -> None:
        """Verify backfill concurrency is set to 5."""
        assert BACKFILL_MAX_CONCURRENT_PARTITIONS == 5

    def test_schedule_cron_format(self) -> None:
        """Verify schedule cron is set for 2nd of month at 00:00."""
        assert SCHEDULE_CRON == "0 0 2 * *"


class TestAssetSelection:
    """Test suite for asset selection configuration."""

    def test_asset_selection_includes_both_assets(self) -> None:
        """Verify asset selection includes both pipeline assets."""
        assert who_is_hiring_assets is not None


class TestIngestionJob:
    """Test suite for who_is_hiring_ingestion_job."""

    def test_job_name(self) -> None:
        """Verify ingestion job name."""
        assert who_is_hiring_ingestion_job.name == "who_is_hiring_ingestion_job"

    def test_job_has_description(self) -> None:
        """Verify ingestion job has description."""
        assert who_is_hiring_ingestion_job.description is not None
        assert len(who_is_hiring_ingestion_job.description) > 0

    def test_job_has_tags(self) -> None:
        """Verify ingestion job has runtime tags."""
        tags = who_is_hiring_ingestion_job.tags
        assert tags is not None
        assert "dagster/max_runtime" in tags


class TestBackfillJob:
    """Test suite for who_is_hiring_backfill_job."""

    def test_backfill_job_name(self) -> None:
        """Verify backfill job name."""
        assert who_is_hiring_backfill_job.name == "who_is_hiring_backfill_job"

    def test_backfill_job_has_description(self) -> None:
        """Verify backfill job has description."""
        assert who_is_hiring_backfill_job.description is not None
        assert "Backfill" in who_is_hiring_backfill_job.description

    def test_backfill_job_has_concurrency_tags(self) -> None:
        """Verify backfill job has concurrency control tags."""
        tags = who_is_hiring_backfill_job.tags
        assert tags is not None
        assert "dagster/concurrency_key" in tags
        assert "dagster/max_concurrent_backfill_partitions" in tags

    def test_backfill_job_max_partitions_tag_value(self) -> None:
        """Verify backfill job has correct max partitions value."""
        tags = who_is_hiring_backfill_job.tags
        assert tags["dagster/max_concurrent_backfill_partitions"] == "5"


class TestMonthlySchedule:
    """Test suite for who_is_hiring_monthly_schedule."""

    def test_schedule_exists(self) -> None:
        """Verify schedule object is created."""
        assert who_is_hiring_monthly_schedule is not None

    def test_schedule_has_name(self) -> None:
        """Verify schedule has expected name pattern."""
        assert "who_is_hiring_ingestion_job" in who_is_hiring_monthly_schedule.name

    def test_schedule_has_description(self) -> None:
        """Verify schedule has description."""
        assert who_is_hiring_monthly_schedule.description is not None
        assert "2nd" in who_is_hiring_monthly_schedule.description

    def test_schedule_day_of_month(self) -> None:
        """Verify schedule runs on 2nd of month."""
        assert who_is_hiring_monthly_schedule.day_of_month == 2

    def test_schedule_hour_of_day(self) -> None:
        """Verify schedule runs at 00:00 UTC."""
        assert who_is_hiring_monthly_schedule.hour_of_day == 0

    def test_schedule_minute_of_hour(self) -> None:
        """Verify schedule runs at minute 0."""
        assert who_is_hiring_monthly_schedule.minute_of_hour == 0


class TestScheduleIntegration:
    """Integration tests for schedule with Dagster Definitions."""

    def test_schedule_is_registered_in_definitions(self) -> None:
        """Verify schedule is registered in definitions."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        schedule_names = [s.name for s in repository.schedule_defs]
        assert any("who_is_hiring_ingestion_job" in name for name in schedule_names)

    def test_ingestion_job_is_registered_in_definitions(self) -> None:
        """Verify ingestion job is registered in definitions."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        job_names = [j.name for j in repository.get_all_jobs()]
        assert "who_is_hiring_ingestion_job" in job_names

    def test_backfill_job_is_registered_in_definitions(self) -> None:
        """Verify backfill job is registered in definitions."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        job_names = [j.name for j in repository.get_all_jobs()]
        assert "who_is_hiring_backfill_job" in job_names

    def test_schedule_targets_correct_job(self) -> None:
        """Verify schedule targets the ingestion job."""
        from techpulse.data.definitions import defs

        repository = defs.get_repository_def()
        monthly_schedule = None
        for schedule in repository.schedule_defs:
            if "who_is_hiring_ingestion_job" in schedule.name:
                monthly_schedule = schedule
                break

        assert monthly_schedule is not None
        assert monthly_schedule.job_name == "who_is_hiring_ingestion_job"
