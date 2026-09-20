"""src.handlers.list_urls のテスト — GET /urls ハンドラー。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.handlers.list_urls import handler
from src.models.url import UrlItem
from tests.helpers import admin_event


class TestListUrlsHandler:
    """list_urls Lambdaハンドラーのテスト。"""

    @patch("src.handlers.list_urls.UrlRepository")
    def test_returns_list_of_active_urls(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = (
            [
                UrlItem(short_id="a", original_url="https://a.com", created_at=1),
                UrlItem(short_id="b", original_url="https://b.com", created_at=2),
            ],
            None,
        )
        mock_repo_cls.return_value = mock_repo

        event: dict[str, dict[str, str] | None] = {"queryStringParameters": None}
        result = handler(admin_event(event), None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["count"] == 2
        assert len(body["items"]) == 2

    @patch("src.handlers.list_urls.UrlRepository")
    def test_default_limit_is_50(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = ([], None)
        mock_repo_cls.return_value = mock_repo

        event: dict[str, dict[str, str] | None] = {"queryStringParameters": None}
        handler(admin_event(event), None)

        mock_repo.list_page.assert_called_once_with(limit=50, cursor=None)

    @patch("src.handlers.list_urls.UrlRepository")
    def test_custom_limit_via_query_string(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = ([], None)
        mock_repo_cls.return_value = mock_repo

        event = {"queryStringParameters": {"limit": "10"}}
        handler(admin_event(event), None)

        mock_repo.list_page.assert_called_once_with(limit=10, cursor=None)

    @patch("src.handlers.list_urls.UrlRepository")
    def test_limit_capped_at_200(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = ([], None)
        mock_repo_cls.return_value = mock_repo

        event = {"queryStringParameters": {"limit": "999"}}
        handler(admin_event(event), None)

        mock_repo.list_page.assert_called_once_with(limit=200, cursor=None)

    @patch("src.handlers.list_urls.UrlRepository")
    def test_invalid_limit_is_a_client_error(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = ([], None)
        mock_repo_cls.return_value = mock_repo

        event = {"queryStringParameters": {"limit": "abc"}}
        result = handler(admin_event(event), None)

        assert result["statusCode"] == 400
        mock_repo.list_page.assert_not_called()

    @patch("src.handlers.list_urls.UrlRepository")
    def test_empty_result(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.list_page.return_value = ([], None)
        mock_repo_cls.return_value = mock_repo

        event: dict[str, dict[str, str] | None] = {"queryStringParameters": None}
        result = handler(admin_event(event), None)

        body = json.loads(result["body"])
        assert body["count"] == 0
        assert body["items"] == []
