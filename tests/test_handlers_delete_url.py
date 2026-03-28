"""src.handlers.delete_url のテスト — DELETE /urls/{short_id} ハンドラー。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.handlers.delete_url import handler


class TestDeleteUrlHandler:
    """delete_url Lambdaハンドラーのテスト。"""

    @patch("src.handlers.delete_url.UrlRepository")
    def test_deletes_existing_url(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.soft_delete.return_value = True
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "abc"}}
        result = handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "削除" in body["message"] or "abc" in body["message"]
        mock_repo.soft_delete.assert_called_once_with("abc")

    @patch("src.handlers.delete_url.UrlRepository")
    def test_returns_404_for_nonexistent(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.soft_delete.return_value = False
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "missing"}}
        result = handler(event, None)

        assert result["statusCode"] == 404

    def test_rejects_invalid_short_id(self) -> None:
        event = {"pathParameters": {"short_id": "has spaces"}}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_empty_short_id(self) -> None:
        event = {"pathParameters": {"short_id": ""}}
        result = handler(event, None)
        assert result["statusCode"] == 400
