"""src.handlers.get_url_stats のテスト — GET /urls/{short_id} ハンドラー。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.handlers.get_url_stats import handler
from src.models.url import UrlItem


class TestGetUrlStatsHandler:
    """get_url_stats Lambdaハンドラーのテスト。"""

    @patch("src.handlers.get_url_stats.UrlRepository")
    def test_returns_stats_for_existing_url(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = UrlItem(
            short_id="abc",
            original_url="https://example.com",
            created_at=1000,
            click_count=42,
        )
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "abc"}}
        result = handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["short_id"] == "abc"
        assert body["click_count"] == 42

    @patch("src.handlers.get_url_stats.UrlRepository")
    def test_returns_404_for_nonexistent(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "missing"}}
        result = handler(event, None)

        assert result["statusCode"] == 404

    def test_rejects_invalid_short_id(self) -> None:
        event = {"pathParameters": {"short_id": "!invalid!"}}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_missing_path_params(self) -> None:
        event: dict[str, None] = {"pathParameters": None}
        result = handler(event, None)
        assert result["statusCode"] == 400
