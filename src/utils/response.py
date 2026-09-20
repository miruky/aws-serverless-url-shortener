"""API Gateway応答。管理情報も転送先も永続キャッシュしない。"""

from __future__ import annotations

import json
import os
from typing import Any


def headers() -> dict[str, str]:
    values = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    }
    origin = os.environ.get("ALLOWED_ORIGIN", "")
    if origin and origin != "*":
        values.update(
            {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET,HEAD,POST,PATCH,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization,If-Match",
                "Vary": "Origin",
            }
        )
    return values


def success_response(body: Any, status_code: int = 200) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": headers(),
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    return success_response({"error": message}, status_code)


def redirect_response(url: str) -> dict[str, Any]:
    return {"statusCode": 302, "headers": {**headers(), "Location": url}, "body": ""}
