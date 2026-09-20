"""公開APIの実際の不具合を修正前後の同じ入力で検証する。"""

import base64
import json
from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest

from src.handlers.create_url import handler as create
from src.handlers.list_urls import handler as list_urls
from src.models.url import UrlItem
from src.repositories.url_repository import UrlRepository
from src.utils.response import redirect_response
from src.utils.validators import validate_short_id, validate_url


def event(body):
    return {"body": body, "requestContext": {"authorizer": {"claims": {"sub": "test-owner"}}}}


@pytest.mark.parametrize("value", [[], None, 1, "text"])
def test_non_object_json_is_a_client_error(value):
    response = None
    with suppress(AttributeError, TypeError):
        response = create(event(json.dumps(value)), None)
    assert response is not None, "Valid JSON with the wrong shape must not crash Lambda"
    assert response["statusCode"] == 400


@pytest.mark.parametrize("url", ["https://example.com?q=1", "https://example.com#section"])
def test_valid_url_without_slash_is_supported(url):
    assert validate_url(url)


@pytest.mark.parametrize(
    "url",
    ["https://example.com:99999/", "https://example.com/\n", "https://user:password@example.com/"],
)
def test_unsafe_or_invalid_url_is_rejected(url):
    assert not validate_url(url)


def test_short_id_cannot_end_in_a_newline():
    assert not validate_short_id("abc\n")


def test_collision_cannot_overwrite_an_existing_destination(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    repo.put(UrlItem(short_id="same", original_url="https://original.example.com"))
    with suppress(Exception):
        repo.put(UrlItem(short_id="same", original_url="https://different.example.com"))
    assert repo.get("same").original_url == "https://original.example.com"


@pytest.mark.parametrize("limit", ["0", "-5"])
def test_nonpositive_list_limit_is_rejected(limit):
    request = event(None)
    request["queryStringParameters"] = {"limit": limit}
    with patch("src.handlers.list_urls.UrlRepository", return_value=MagicMock()) as repository:
        repository.return_value.list_active.return_value = []
        assert list_urls(request, None)["statusCode"] == 400
        repository.assert_not_called()


def test_redirect_is_revocable_and_not_permanently_cached():
    response = redirect_response("https://example.com/")
    assert response["statusCode"] == 302
    assert "no-store" in response["headers"]["Cache-Control"]


def test_base64_api_gateway_body_is_decoded():
    request = event(base64.b64encode(b'{"url":"https://example.com"}').decode())
    request["isBase64Encoded"] = True
    with patch("src.handlers.create_url.UrlRepository"):
        assert create(request, None)["statusCode"] == 201
