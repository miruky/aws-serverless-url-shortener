"""Tests for src.handlers.create_url — POST /urls handler."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.handlers.create_url import handler


class TestCreateUrlHandler:
    """Tests for the create_url Lambda handler."""

    @patch("src.handlers.create_url.UrlRepository")
    @patch("src.handlers.create_url.generate_short_id", return_value="aB3kZ9x")
    def test_creates_url_successfully(
        self, mock_gen: MagicMock, mock_repo_cls: MagicMock
    ) -> None:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = {"body": json.dumps({"url": "https://example.com"})}
        result = handler(event, None)

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["short_id"] == "aB3kZ9x"
        assert body["original_url"] == "https://example.com"
        mock_repo.put.assert_called_once()

    def test_rejects_missing_body(self) -> None:
        event: dict[str, str | None] = {"body": None}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_invalid_json(self) -> None:
        event = {"body": "not-json"}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_missing_url_field(self) -> None:
        event = {"body": json.dumps({"wrong_key": "value"})}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_invalid_url(self) -> None:
        event = {"body": json.dumps({"url": "not-a-url"})}
        result = handler(event, None)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body

    @patch("src.handlers.create_url.UrlRepository")
    @patch("src.handlers.create_url.generate_short_id", return_value="xyz1234")
    def test_response_includes_cors_headers(
        self, mock_gen: MagicMock, mock_repo_cls: MagicMock
    ) -> None:
        mock_repo_cls.return_value = MagicMock()
        event = {"body": json.dumps({"url": "https://example.com"})}
        result = handler(event, None)
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"
