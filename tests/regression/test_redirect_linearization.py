"""転送を受理した時点と、HTTP応答を組み立てる時点の時計の差。"""

from unittest.mock import patch

from src.handlers.redirect_url import handler
from src.models.url import UrlItem


def test_a_get_accepted_before_expiry_returns_the_committed_destination():
    with (
        patch("src.handlers.redirect_url.UrlRepository") as factory,
        patch("src.handlers.redirect_url.time.time", return_value=101),
    ):
        factory.return_value.increment_click.return_value = UrlItem(
            "edge", "https://example.com", expires_at=100, click_count=1
        )
        response = handler({"httpMethod": "GET", "pathParameters": {"short_id": "edge"}}, None)
    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == "https://example.com"
    factory.return_value.increment_click.assert_called_once_with("edge")
