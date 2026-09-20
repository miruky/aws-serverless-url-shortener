"""実用的なURL・旧データ・HTTP境界条件の回帰テスト。"""

import json

from src.handlers.create_url import handler as create
from src.handlers.redirect_url import handler as redirect
from src.handlers.update_url import handler as update
from tests.helpers import admin_event


def test_international_destination_is_an_ascii_location(dynamodb_resource):
    response = create(
        admin_event({"body": json.dumps({"url": "https://例え.jp/資料?q=日本語"})}), None
    )
    assert response["statusCode"] == 201
    item = json.loads(response["body"])
    response = redirect({"pathParameters": {"short_id": item["short_id"]}}, None)
    assert response["headers"]["Location"].isascii()
    assert "xn--" in response["headers"]["Location"]
    assert "%E8%B3%87%E6%96%99" in response["headers"]["Location"]


def test_legacy_record_without_optional_flags_still_redirects(dynamodb_resource):
    table = dynamodb_resource.Table("test-urls")
    table.put_item(Item={"short_id": "old", "original_url": "https://example.com"})
    assert redirect({"pathParameters": {"short_id": "old"}}, None)["statusCode"] == 302
    assert table.get_item(Key={"short_id": "old"})["Item"]["click_count"] == 1


def test_head_error_response_has_no_body(dynamodb_resource):
    response = redirect({"pathParameters": {"short_id": "missing"}, "httpMethod": "HEAD"}, None)
    assert response["statusCode"] == 404
    assert response["body"] == ""


def test_expiry_cannot_break_browser_date_rendering(dynamodb_resource):
    response = create(
        admin_event({"body": json.dumps({"url": "https://example.com", "expires_at": 10**20})}),
        None,
    )
    assert response["statusCode"] == 400


def test_version_is_bounded_to_safe_integer(dynamodb_resource):
    response = update(
        admin_event(
            {
                "pathParameters": {"short_id": "missing"},
                "body": json.dumps({"version": 10**20, "title": "x"}),
            }
        ),
        None,
    )
    assert response["statusCode"] == 400
