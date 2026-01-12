"""Tests for TechPulse data pipeline definitions."""

from dagster import Definitions

from techpulse.data.definitions import defs


class TestDagsterDefinitions:
    """Test suite for Dagster asset definitions."""

    def test_definitions_is_valid_instance(self) -> None:
        """Verify defs is a valid Dagster Definitions object."""
        assert isinstance(defs, Definitions)

    def test_definitions_has_assets_attribute(self) -> None:
        """Verify definitions object has expected structure."""
        repository = defs.get_repository_def()
        assert repository is not None

    def test_definitions_loads_without_error(self) -> None:
        """Verify definitions can be resolved without errors."""
        repository = defs.get_repository_def()
        assets = repository.get_all_jobs()
        assert isinstance(assets, list)
