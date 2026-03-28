"""Tests for src.handlers.redirect_url — GET /{short_id} handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.handlers.redirect_url import handler
from src.models.url import UrlItem


class TestRedirectUrlHandler:
    """Tests for the redirect_url Lambda handler."""

    @patch("src.handlers.redirect_url.UrlRepository")
    def test_redirects_active_url(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = UrlItem(
            short_id="abc", original_url="https://example.com", created_at=1000
        )
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "abc"}}
        result = handler(event, None)

        assert result["statusCode"] == 301
        assert result["headers"]["Location"] == "https://example.com"
        mock_repo.increment_click.assert_called_once_with("abc")

    @patch("src.handlers.redirect_url.UrlRepository")
    def test_returns_404_for_nonexistent(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "missing"}}
        result = handler(event, None)

        assert result["statusCode"] == 404

    @patch("src.handlers.redirect_url.UrlRepository")
    def test_returns_404_for_inactive_url(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = UrlItem(
            short_id="abc",
            original_url="https://example.com",
            created_at=1000,
            is_active=False,
        )
        mock_repo_cls.return_value = mock_repo

        event = {"pathParameters": {"short_id": "abc"}}
        result = handler(event, None)

        assert result["statusCode"] == 404
        mock_repo.increment_click.assert_not_called()

    def test_rejects_invalid_short_id(self) -> None:
        event = {"pathParameters": {"short_id": "abc-!@#"}}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_rejects_missing_path_params(self) -> None:
        event: dict[str, None] = {"pathParameters": None}
        result = handler(event, None)
        assert result["statusCode"] == 400
