"""Tests for src.utils.validators — input validation."""

from __future__ import annotations

import pytest

from src.utils.validators import validate_short_id, validate_url


# ---------------------------------------------------------------------------
# validate_url
# ---------------------------------------------------------------------------

class TestValidateUrl:
    """Tests for the validate_url function."""

    @pytest.mark.parametrize("url", [
        "https://example.com",
        "http://example.com",
        "https://sub.domain.example.com/path?q=1",
        "https://example.com:8080/page",
        "https://example.co.jp",
    ])
    def test_valid_urls(self, url: str) -> None:
        assert validate_url(url) is True

    @pytest.mark.parametrize("url", [
        "",
        "ftp://example.com",
        "not-a-url",
        "https://",
        "https://.com",
        "://missing-scheme.com",
    ])
    def test_invalid_urls(self, url: str) -> None:
        assert validate_url(url) is False

    def test_rejects_none(self) -> None:
        assert validate_url(None) is False  # type: ignore[arg-type]

    def test_rejects_non_string(self) -> None:
        assert validate_url(12345) is False  # type: ignore[arg-type]

    def test_rejects_url_exceeding_max_length(self) -> None:
        long_url = "https://example.com/" + "a" * 2048
        assert validate_url(long_url) is False


# ---------------------------------------------------------------------------
# validate_short_id
# ---------------------------------------------------------------------------

class TestValidateShortId:
    """Tests for the validate_short_id function."""

    @pytest.mark.parametrize("short_id", [
        "abc1234",
        "A",
        "abcdefghijklmnopqrst",  # 20 chars
    ])
    def test_valid_short_ids(self, short_id: str) -> None:
        assert validate_short_id(short_id) is True

    @pytest.mark.parametrize("short_id", [
        "",
        "abc-123",
        "abc 123",
        "abc!@#",
        "a" * 21,  # 21 chars — over limit
    ])
    def test_invalid_short_ids(self, short_id: str) -> None:
        assert validate_short_id(short_id) is False

    def test_rejects_none(self) -> None:
        assert validate_short_id(None) is False  # type: ignore[arg-type]

    def test_rejects_non_string(self) -> None:
        assert validate_short_id(42) is False  # type: ignore[arg-type]
