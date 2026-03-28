"""API Gatewayレスポンスビルダーヘルパー。"""

from __future__ import annotations

import json
from typing import Any

_CORS_HEADERS: dict[str, str] = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def success_response(body: Any, status_code: int = 200) -> dict[str, Any]:
    """成功時のAPI Gatewayプロキシレスポンスを構築する。

    Args:
        body: JSONシリアライズ可能なペイロード。
        status_code: HTTPステータスコード（デフォルト: 200）。

    Returns:
        API Gateway互換のレスポンス辞書。
    """
    return {
        "statusCode": status_code,
        "headers": {**_CORS_HEADERS},
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    """エラー時のAPI Gatewayプロキシレスポンスを構築する。

    Args:
        message: 人間が読めるエラー説明。
        status_code: HTTPステータスコード（デフォルト: 400）。

    Returns:
        API Gateway互換のレスポンス辞書。
    """
    return {
        "statusCode": status_code,
        "headers": {**_CORS_HEADERS},
        "body": json.dumps({"error": message}, ensure_ascii=False),
    }


def redirect_response(url: str) -> dict[str, Any]:
    """301リダイレクトレスポンスを構築する。

    Args:
        url: ``Location`` ヘッダーに設定するリダイレクト先URL。

    Returns:
        301ステータスのAPI Gateway互換レスポンス辞書。
    """
    return {
        "statusCode": 301,
        "headers": {
            "Location": url,
            "Cache-Control": "no-cache",
        },
        "body": "",
    }
