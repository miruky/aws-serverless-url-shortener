"""管理者の実際の操作と、失敗時に守るデータの境界。"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from src.handlers.create_url import handler as create
from src.handlers.update_url import handler as update
from src.models.url import UrlItem
from src.repositories.url_repository import IdConflictError, UrlRepository
from tests.helpers import admin_event


def body(value):
    return admin_event({"body": json.dumps(value), "pathParameters": {"short_id": "editable"}})


def test_conflicting_alias_does_not_replace_a_link(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    repo.put(UrlItem("chosen", "https://original.example.com"))
    response = create(
        body({"url": "https://different.example.com", "custom_alias": "chosen"}), None
    )
    assert response["statusCode"] == 409
    assert repo.get("chosen").original_url == "https://original.example.com"


def test_collision_retry_is_bounded():
    with patch("src.handlers.create_url.UrlRepository") as factory:
        factory.return_value.put.side_effect = IdConflictError
        assert create(body({"url": "https://example.com"}), None)["statusCode"] == 503
        assert factory.return_value.put.call_count == 5


def test_edit_conflict_preserves_first_writer(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    repo.put(UrlItem("editable", "https://example.com"))
    first = update(body({"version": 1, "title": "先に保存"}), None)
    assert first["statusCode"] == 200
    assert json.loads(first["body"])["version"] == 2
    assert update(body({"version": 1, "title": "古い画面"}), None)["statusCode"] == 409
    assert repo.get("editable").title == "先に保存"


def test_expiry_can_be_removed_and_stopped_link_resumed(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    repo.put(UrlItem("editable", "https://example.com", is_active=False, expires_at=1))
    response = update(body({"version": 1, "is_active": True, "expires_at": None}), None)
    assert response["statusCode"] == 200
    assert repo.get("editable").is_active
    assert repo.get("editable").expires_at is None


@pytest.mark.parametrize(
    "value",
    [
        {"title": "x"},
        {"version": True, "title": "x"},
        {"version": 1},
        {"version": 1, "is_active": "false"},
        {"version": 1, "title": 12},
        {"version": 1, "unknown": "x"},
        {"version": 1, "expires_at": False},
    ],
)
def test_invalid_edits_fail_before_storage(value):
    with patch("src.handlers.update_url.UrlRepository") as factory:
        assert update(body(value), None)["statusCode"] == 400
        factory.assert_not_called()


def test_storage_error_never_echoes_destination_or_backend_detail(caplog):
    private_url = "https://example.com/?secret=do-not-log"
    with patch("src.handlers.create_url.UrlRepository") as factory:
        factory.return_value.put.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": private_url}}, "PutItem"
        )
        response = create(body({"url": private_url}), None)
    assert response["statusCode"] == 503
    assert response["headers"]["Retry-After"] == "3"
    assert private_url not in response["body"] + caplog.text


def test_malformed_and_oversized_cursor_is_rejected(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    for cursor in ["not!base64", "e30=", "x" * 257, "W10="]:
        with pytest.raises(ValueError, match="ページ"):
            repo.list_page(cursor=cursor)
