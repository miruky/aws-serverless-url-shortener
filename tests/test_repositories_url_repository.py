"""src.repositories.url_repository のテスト — DynamoDB統合テスト(moto)。"""

from __future__ import annotations

from typing import Any

from src.models.url import UrlItem
from src.repositories.url_repository import UrlRepository


class TestUrlRepositoryPut:
    """UrlRepository.putのテスト。"""

    def test_put_stores_item(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        item = UrlItem(short_id="abc123", original_url="https://example.com", created_at=1000)
        repo.put(item)

        stored = repo.get("abc123")
        assert stored is not None
        assert stored.short_id == "abc123"
        assert stored.original_url == "https://example.com"

    def test_put_overwrites_existing(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="abc", original_url="https://old.com", created_at=1))
        repo.put(UrlItem(short_id="abc", original_url="https://new.com", created_at=2))

        stored = repo.get("abc")
        assert stored is not None
        assert stored.original_url == "https://new.com"


class TestUrlRepositoryGet:
    """UrlRepository.getのテスト。"""

    def test_get_existing_item(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="abc", original_url="https://example.com", created_at=1000))

        item = repo.get("abc")
        assert item is not None
        assert item.short_id == "abc"

    def test_get_nonexistent_returns_none(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        assert repo.get("nonexistent") is None


class TestUrlRepositoryIncrementClick:
    """UrlRepository.increment_clickのテスト。"""

    def test_increment_increases_count(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="abc", original_url="https://example.com", created_at=1000))

        repo.increment_click("abc")
        item = repo.get("abc")
        assert item is not None
        assert item.click_count == 1

    def test_increment_multiple_times(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="abc", original_url="https://example.com", created_at=1000))

        for _ in range(5):
            repo.increment_click("abc")

        item = repo.get("abc")
        assert item is not None
        assert item.click_count == 5


class TestUrlRepositorySoftDelete:
    """UrlRepository.soft_deleteのテスト。"""

    def test_soft_delete_existing_item(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="abc", original_url="https://example.com", created_at=1000))

        result = repo.soft_delete("abc")
        assert result is True

        item = repo.get("abc")
        assert item is not None
        assert item.is_active is False

    def test_soft_delete_nonexistent_returns_false(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        result = repo.soft_delete("nonexistent")
        assert result is False


class TestUrlRepositoryListActive:
    """UrlRepository.list_activeのテスト。"""

    def test_list_active_returns_only_active_items(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        repo.put(UrlItem(short_id="a", original_url="https://a.com", created_at=1))
        repo.put(UrlItem(short_id="b", original_url="https://b.com", created_at=2))
        repo.put(
            UrlItem(short_id="c", original_url="https://c.com", created_at=3, is_active=False),
        )

        items = repo.list_active()
        ids = {item.short_id for item in items}
        assert "a" in ids
        assert "b" in ids
        assert "c" not in ids

    def test_list_active_empty_table(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        items = repo.list_active()
        assert items == []

    def test_list_active_respects_limit(self, dynamodb_resource: Any) -> None:
        repo = UrlRepository(table_name="test-urls", dynamodb_resource=dynamodb_resource)
        for i in range(5):
            repo.put(UrlItem(short_id=f"id{i}", original_url=f"https://{i}.com", created_at=i))

        items = repo.list_active(limit=3)
        assert len(items) <= 3
