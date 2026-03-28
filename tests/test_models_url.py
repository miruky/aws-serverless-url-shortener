"""Tests for src.models.url — UrlItem dataclass."""

from __future__ import annotations

import dataclasses
import time

import pytest

from src.models.url import UrlItem


# ---------------------------------------------------------------------------
# UrlItem.__init__
# ---------------------------------------------------------------------------

class TestUrlItemInit:
    """Tests for UrlItem construction and default values."""

    def test_create_with_required_fields(self) -> None:
        item = UrlItem(short_id="abc1234", original_url="https://example.com")
        assert item.short_id == "abc1234"
        assert item.original_url == "https://example.com"

    def test_default_click_count_is_zero(self) -> None:
        item = UrlItem(short_id="abc1234", original_url="https://example.com")
        assert item.click_count == 0

    def test_default_is_active_is_true(self) -> None:
        item = UrlItem(short_id="abc1234", original_url="https://example.com")
        assert item.is_active is True

    def test_created_at_defaults_to_current_timestamp(self) -> None:
        before = int(time.time())
        item = UrlItem(short_id="abc1234", original_url="https://example.com")
        after = int(time.time())
        assert before <= item.created_at <= after

    def test_explicit_created_at_is_respected(self) -> None:
        item = UrlItem(short_id="abc1234", original_url="https://example.com", created_at=42)
        assert item.created_at == 42

    def test_frozen_dataclass_prevents_mutation(self) -> None:
        item = UrlItem(short_id="abc1234", original_url="https://example.com")
        with pytest.raises(dataclasses.FrozenInstanceError):
            item.click_count = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# UrlItem.to_dict
# ---------------------------------------------------------------------------

class TestUrlItemToDict:
    """Tests for the to_dict serialisation method."""

    def test_to_dict_returns_all_fields(self) -> None:
        item = UrlItem(
            short_id="abc",
            original_url="https://example.com",
            created_at=1000,
            click_count=5,
            is_active=True,
        )
        assert item.to_dict() == {
            "short_id": "abc",
            "original_url": "https://example.com",
            "created_at": 1000,
            "click_count": 5,
            "is_active": True,
        }

    def test_to_dict_with_inactive_item(self) -> None:
        item = UrlItem(
            short_id="xyz",
            original_url="https://example.com/page",
            created_at=999,
            click_count=0,
            is_active=False,
        )
        result = item.to_dict()
        assert result["is_active"] is False
        assert result["click_count"] == 0


# ---------------------------------------------------------------------------
# UrlItem.from_dict
# ---------------------------------------------------------------------------

class TestUrlItemFromDict:
    """Tests for the from_dict deserialisation class method."""

    def test_from_dict_with_all_fields(self) -> None:
        data = {
            "short_id": "abc",
            "original_url": "https://example.com",
            "created_at": 1000,
            "click_count": 5,
            "is_active": True,
        }
        item = UrlItem.from_dict(data)
        assert item.short_id == "abc"
        assert item.original_url == "https://example.com"
        assert item.click_count == 5

    def test_from_dict_with_missing_optional_fields(self) -> None:
        data = {"short_id": "abc", "original_url": "https://example.com"}
        item = UrlItem.from_dict(data)
        assert item.click_count == 0
        assert item.is_active is True
        assert item.created_at == 0

    def test_from_dict_coerces_types(self) -> None:
        data = {
            "short_id": "x",
            "original_url": "https://example.com",
            "created_at": "12345",
            "click_count": "7",
        }
        item = UrlItem.from_dict(data)
        assert item.created_at == 12345
        assert item.click_count == 7

    def test_roundtrip_to_dict_from_dict(self) -> None:
        original = UrlItem(
            short_id="abc",
            original_url="https://example.com",
            created_at=1000,
            click_count=3,
            is_active=True,
        )
        restored = UrlItem.from_dict(original.to_dict())
        assert restored.short_id == original.short_id
        assert restored.original_url == original.original_url
        assert restored.created_at == original.created_at
        assert restored.click_count == original.click_count
        assert restored.is_active == original.is_active
