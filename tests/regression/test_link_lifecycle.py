"""管理APIの作成、停止、期限、継続ページを実際のモックDBで確認する。"""

import json
import time

from src.handlers.create_url import handler as create
from src.handlers.list_urls import handler as listing
from src.handlers.redirect_url import handler as redirect
from src.models.url import UrlItem
from src.repositories.url_repository import UrlRepository


def request(body=None, **kwargs):
    return {
        "body": json.dumps(body or {}),
        "requestContext": {"authorizer": {"claims": {"sub": "owner"}}},
        **kwargs,
    }


def test_custom_alias_title_and_expiry_roundtrip(dynamodb_resource):
    expiry = int(time.time()) + 3600
    response = create(
        request(
            {
                "url": "https://example.com",
                "custom_alias": "release",
                "title": "リリース",
                "expires_at": expiry,
            }
        ),
        None,
    )
    assert response["statusCode"] == 201
    saved = json.loads(response["body"])
    assert saved["short_id"] == "release"
    assert saved["title"] == "リリース"
    assert saved["expires_at"] == expiry


def test_expired_record_cannot_redirect_or_increment(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    dynamodb_resource.Table("test-urls").put_item(
        Item={**UrlItem("expired", "https://example.com").to_dict(), "expires_at": 1}
    )
    response = redirect({"pathParameters": {"short_id": "expired"}}, None)
    assert response["statusCode"] == 410
    assert repo.get("expired").click_count == 0


def test_head_does_not_count_a_visit(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    repo.put(UrlItem("head", "https://example.com"))
    response = redirect({"pathParameters": {"short_id": "head"}, "httpMethod": "HEAD"}, None)
    assert response["statusCode"] == 302
    assert repo.get("head").click_count == 0


def test_page_cursor_reaches_every_record(dynamodb_resource):
    repo = UrlRepository("test-urls", dynamodb_resource)
    for i in range(5):
        repo.put(UrlItem(f"id{i}", "https://example.com"))
    cursor = None
    seen = []
    for _ in range(5):
        query = {"limit": "2"}
        if cursor:
            query["cursor"] = cursor
        response = listing(request(queryStringParameters=query), None)
        assert response["statusCode"] == 200
        page = json.loads(response["body"])
        seen.extend(item["short_id"] for item in page["items"])
        cursor = page.get("next_cursor")
        if not cursor:
            break
    assert len(seen) == len(set(seen)) == 5


def test_reserved_alias_is_rejected(dynamodb_resource):
    response = create(request({"url": "https://example.com", "custom_alias": "app"}), None)
    assert response["statusCode"] == 400
