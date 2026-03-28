"""src.utils.short_id のテスト — 短縮ID生成。"""

from __future__ import annotations

import string

from src.utils.short_id import CHARSET, DEFAULT_LENGTH, generate_short_id


class TestGenerateShortId:
    """generate_short_id関数のテスト。"""

    def test_returns_string_of_default_length(self) -> None:
        result = generate_short_id("https://example.com")
        assert isinstance(result, str)
        assert len(result) == DEFAULT_LENGTH

    def test_custom_length(self) -> None:
        result = generate_short_id("https://example.com", length=10)
        assert len(result) == 10

    def test_contains_only_alphanumeric_chars(self) -> None:
        result = generate_short_id("https://example.com")
        allowed = set(string.ascii_letters + string.digits)
        assert all(c in allowed for c in result)

    def test_different_urls_produce_different_ids(self) -> None:
        id1 = generate_short_id("https://example.com/a")
        id2 = generate_short_id("https://example.com/b")
        assert id1 != id2

    def test_same_url_produces_different_ids_over_time(self) -> None:
        """タイムスタンプ成分により同一URLでも一意性が保証される。"""
        ids = {generate_short_id("https://example.com") for _ in range(20)}
        assert len(ids) > 1

    def test_length_one(self) -> None:
        result = generate_short_id("https://example.com", length=1)
        assert len(result) == 1
        assert result in CHARSET

    def test_empty_url_still_returns_valid_id(self) -> None:
        result = generate_short_id("")
        assert len(result) == DEFAULT_LENGTH
        assert all(c in CHARSET for c in result)
