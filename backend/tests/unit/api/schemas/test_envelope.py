"""Unit tests for response envelope schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

from techpulse.api.schemas.envelope import (
    Meta,
    ResponseEnvelope,
    create_envelope,
)


class TestMeta:
    """Test suite for Meta model."""

    def test_default_request_id_generated(self) -> None:
        """Verify request_id is auto-generated when not provided."""
        meta = Meta()
        assert meta.request_id is not None
        assert len(meta.request_id) == 36

    def test_default_timestamp_generated(self) -> None:
        """Verify timestamp is auto-generated when not provided."""
        before = datetime.now(timezone.utc)
        meta = Meta()
        after = datetime.now(timezone.utc)
        assert before <= meta.timestamp <= after

    def test_custom_request_id_preserved(self) -> None:
        """Verify custom request_id is preserved."""
        custom_id = "custom-request-id-12345"
        meta = Meta(request_id=custom_id)
        assert meta.request_id == custom_id

    def test_pagination_fields_default_none(self) -> None:
        """Verify pagination fields default to None."""
        meta = Meta()
        assert meta.total_count is None
        assert meta.page is None
        assert meta.page_size is None
        assert meta.has_more is None

    def test_pagination_fields_set(self) -> None:
        """Verify pagination fields can be set."""
        meta = Meta(total_count=100, page=1, page_size=20, has_more=True)
        assert meta.total_count == 100
        assert meta.page == 1
        assert meta.page_size == 20
        assert meta.has_more is True

    def test_total_count_must_be_non_negative(self) -> None:
        """Verify total_count rejects negative values."""
        with pytest.raises(ValueError):
            Meta(total_count=-1)

    def test_page_must_be_positive(self) -> None:
        """Verify page rejects zero and negative values."""
        with pytest.raises(ValueError):
            Meta(page=0)

    def test_page_size_must_be_positive(self) -> None:
        """Verify page_size rejects zero and negative values."""
        with pytest.raises(ValueError):
            Meta(page_size=0)

    def test_serialization_to_dict(self) -> None:
        """Verify Meta serializes to dict correctly."""
        meta = Meta(total_count=50, page=2, page_size=10, has_more=True)
        data = meta.model_dump()
        assert "request_id" in data
        assert "timestamp" in data
        assert data["total_count"] == 50
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["has_more"] is True


class TestResponseEnvelope:
    """Test suite for ResponseEnvelope model."""

    def test_wraps_dict_data(self) -> None:
        """Verify ResponseEnvelope wraps dict data."""
        data = {"id": 1, "name": "test"}
        envelope = ResponseEnvelope(data=data)
        assert envelope.data == data

    def test_wraps_list_data(self) -> None:
        """Verify ResponseEnvelope wraps list data."""
        data = [{"id": 1}, {"id": 2}]
        envelope = ResponseEnvelope(data=data)
        assert envelope.data == data

    def test_wraps_primitive_data(self) -> None:
        """Verify ResponseEnvelope wraps primitive data."""
        envelope = ResponseEnvelope(data="simple string")
        assert envelope.data == "simple string"

    def test_wraps_pydantic_model(self) -> None:
        """Verify ResponseEnvelope wraps Pydantic models."""

        class Item(BaseModel):
            id: int
            name: str

        item = Item(id=1, name="test")
        envelope = ResponseEnvelope(data=item)
        assert envelope.data.id == 1
        assert envelope.data.name == "test"

    def test_default_meta_generated(self) -> None:
        """Verify default Meta is generated when not provided."""
        envelope = ResponseEnvelope(data={"test": True})
        assert envelope.meta is not None
        assert envelope.meta.request_id is not None

    def test_custom_meta_preserved(self) -> None:
        """Verify custom Meta is preserved."""
        custom_meta = Meta(total_count=100)
        envelope = ResponseEnvelope(data=[], meta=custom_meta)
        assert envelope.meta.total_count == 100

    def test_serialization_to_dict(self) -> None:
        """Verify ResponseEnvelope serializes correctly."""
        envelope = ResponseEnvelope(
            data={"id": 1},
            meta=Meta(total_count=1),
        )
        data = envelope.model_dump()
        assert "data" in data
        assert "meta" in data
        assert data["data"]["id"] == 1
        assert data["meta"]["total_count"] == 1

    def test_json_serialization(self) -> None:
        """Verify ResponseEnvelope serializes to JSON."""
        envelope = ResponseEnvelope(data={"name": "test"})
        json_str = envelope.model_dump_json()
        assert "name" in json_str
        assert "test" in json_str
        assert "meta" in json_str


class TestCreateEnvelope:
    """Test suite for create_envelope helper function."""

    def test_creates_envelope_with_data(self) -> None:
        """Verify create_envelope creates valid envelope."""
        data = {"id": 1}
        envelope = create_envelope(data)
        assert envelope.data == data
        assert envelope.meta is not None

    def test_sets_total_count(self) -> None:
        """Verify create_envelope sets total_count."""
        envelope = create_envelope([], total_count=100)
        assert envelope.meta.total_count == 100

    def test_sets_page_and_page_size(self) -> None:
        """Verify create_envelope sets page and page_size."""
        envelope = create_envelope([], page=2, page_size=20)
        assert envelope.meta.page == 2
        assert envelope.meta.page_size == 20

    def test_computes_has_more_true(self) -> None:
        """Verify has_more is True when more pages exist."""
        envelope = create_envelope([], total_count=100, page=1, page_size=20)
        assert envelope.meta.has_more is True

    def test_computes_has_more_false(self) -> None:
        """Verify has_more is False when on last page."""
        envelope = create_envelope([], total_count=100, page=5, page_size=20)
        assert envelope.meta.has_more is False

    def test_computes_has_more_false_exact(self) -> None:
        """Verify has_more is False when exactly at end."""
        envelope = create_envelope([], total_count=40, page=2, page_size=20)
        assert envelope.meta.has_more is False

    def test_has_more_none_without_pagination(self) -> None:
        """Verify has_more is None without full pagination params."""
        envelope = create_envelope([], total_count=100)
        assert envelope.meta.has_more is None

    def test_custom_request_id(self) -> None:
        """Verify custom request_id is used."""
        custom_id = "my-request-id"
        envelope = create_envelope([], request_id=custom_id)
        assert envelope.meta.request_id == custom_id

    def test_generated_request_id_when_none(self) -> None:
        """Verify request_id is generated when not provided."""
        envelope = create_envelope([])
        assert envelope.meta.request_id is not None
        assert len(envelope.meta.request_id) == 36
