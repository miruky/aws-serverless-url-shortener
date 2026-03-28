"""API Gateway response builder helpers."""

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
    """Build a successful API Gateway proxy response.

    Args:
        body: JSON-serialisable payload.
        status_code: HTTP status code (default 200).

    Returns:
        API Gateway-compatible response dict.
    """
    return {
        "statusCode": status_code,
        "headers": {**_CORS_HEADERS},
        "body": json.dumps(body, ensure_ascii=False),
    }


def error_response(message: str, status_code: int = 400) -> dict[str, Any]:
    """Build an error API Gateway proxy response.

    Args:
        message: Human-readable error description.
        status_code: HTTP status code (default 400).

    Returns:
        API Gateway-compatible response dict.
    """
    return {
        "statusCode": status_code,
        "headers": {**_CORS_HEADERS},
        "body": json.dumps({"error": message}, ensure_ascii=False),
    }


def redirect_response(url: str) -> dict[str, Any]:
    """Build a 301 redirect response.

    Args:
        url: Destination URL for the ``Location`` header.

    Returns:
        API Gateway-compatible response dict with 301 status.
    """
    return {
        "statusCode": 301,
        "headers": {
            "Location": url,
            "Cache-Control": "no-cache",
        },
        "body": "",
    }
