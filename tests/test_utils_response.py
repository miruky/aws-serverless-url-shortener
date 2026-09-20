"""src.utils.response のテスト — API Gatewayレスポンスビルダー。"""

from __future__ import annotations

import json

from src.utils.response import error_response, redirect_response, success_response

# ---------------------------------------------------------------------------
# success_response
# ---------------------------------------------------------------------------


class TestSuccessResponse:
    """success_responseビルダーのテスト。"""

    def test_default_status_code_is_200(self) -> None:
        resp = success_response({"key": "value"})
        assert resp["statusCode"] == 200

    def test_custom_status_code(self) -> None:
        resp = success_response({"key": "value"}, status_code=201)
        assert resp["statusCode"] == 201

    def test_body_is_json(self) -> None:
        resp = success_response({"key": "value"})
        parsed = json.loads(resp["body"])
        assert parsed == {"key": "value"}

    def test_wildcard_origin_is_not_enabled_by_default(self) -> None:
        resp = success_response({})
        assert "Access-Control-Allow-Origin" not in resp["headers"]
        assert resp["headers"]["Content-Type"] == "application/json; charset=utf-8"

    def test_japanese_text_not_ascii_escaped(self) -> None:
        resp = success_response({"msg": "日本語テスト"})
        assert "日本語テスト" in resp["body"]


# ---------------------------------------------------------------------------
# error_response
# ---------------------------------------------------------------------------


class TestErrorResponse:
    """error_responseビルダーのテスト。"""

    def test_default_status_code_is_400(self) -> None:
        resp = error_response("Bad request")
        assert resp["statusCode"] == 400

    def test_custom_status_code(self) -> None:
        resp = error_response("Not found", status_code=404)
        assert resp["statusCode"] == 404

    def test_body_contains_error_key(self) -> None:
        resp = error_response("Something went wrong")
        parsed = json.loads(resp["body"])
        assert parsed == {"error": "Something went wrong"}

    def test_wildcard_origin_is_not_enabled_by_default(self) -> None:
        resp = error_response("err")
        assert "Access-Control-Allow-Origin" not in resp["headers"]


# ---------------------------------------------------------------------------
# redirect_response
# ---------------------------------------------------------------------------


class TestRedirectResponse:
    """redirect_responseビルダーのテスト。"""

    def test_status_code_is_302(self) -> None:
        resp = redirect_response("https://example.com")
        assert resp["statusCode"] == 302

    def test_location_header_set(self) -> None:
        resp = redirect_response("https://example.com/page")
        assert resp["headers"]["Location"] == "https://example.com/page"

    def test_cache_control_no_store(self) -> None:
        resp = redirect_response("https://example.com")
        assert resp["headers"]["Cache-Control"] == "no-store"

    def test_body_is_empty(self) -> None:
        resp = redirect_response("https://example.com")
        assert resp["body"] == ""
