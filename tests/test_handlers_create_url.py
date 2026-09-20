"""src.handlers.create_url のテスト — POST /urls ハンドラー。"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.handlers.create_url import handler
from tests.helpers import admin_event


class TestCreateUrlHandler:
    """create_url Lambdaハンドラーのテスト。"""

    @patch("src.handlers.create_url.UrlRepository")
    @patch("src.handlers.create_url.generate_short_id", return_value="aB3kZ9x")
    def test_creates_url_successfully(self, mock_gen: MagicMock, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = {"body": json.dumps({"url": "https://example.com"})}
        result = handler(admin_event(event), None)

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["short_id"] == "aB3kZ9x"
        assert body["original_url"] == "https://example.com"
        mock_repo.put.assert_called_once()

    def test_rejects_missing_body(self) -> None:
        event: dict[str, str | None] = {"body": None}
        result = handler(admin_event(event), None)
        assert result["statusCode"] == 400

    def test_rejects_invalid_json(self) -> None:
        event = {"body": "not-json"}
        result = handler(admin_event(event), None)
        assert result["statusCode"] == 400

    def test_rejects_missing_url_field(self) -> None:
        event = {"body": json.dumps({"wrong_key": "value"})}
        result = handler(admin_event(event), None)
        assert result["statusCode"] == 400

    def test_rejects_invalid_url(self) -> None:
        event = {"body": json.dumps({"url": "not-a-url"})}
        result = handler(admin_event(event), None)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body

    @patch("src.handlers.create_url.UrlRepository")
    @patch("src.handlers.create_url.generate_short_id", return_value="xyz1234")
    def test_same_origin_response_does_not_allow_every_origin(
        self, mock_gen: MagicMock, mock_repo_cls: MagicMock
    ) -> None:
        mock_repo_cls.return_value = MagicMock()
        event = {"body": json.dumps({"url": "https://example.com"})}
        result = handler(admin_event(event), None)
        assert "Access-Control-Allow-Origin" not in result["headers"]
