"""GET /urls: 継続可能なリンク管理一覧。停止済みレコードも含む。"""

from __future__ import annotations

from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.request import api_handler
from src.utils.response import success_response


@api_handler(management=True)
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    query = event.get("queryStringParameters") or {}
    try:
        limit = min(int(query.get("limit", "50")), 200)
    except (TypeError, ValueError) as exc:
        raise ValueError("limitには1〜200の整数を指定してください。") from exc
    if limit < 1:
        raise ValueError("limitには1〜200の整数を指定してください。")
    repo = UrlRepository()
    items, cursor = repo.list_page(limit=limit, cursor=query.get("cursor"))
    return success_response(
        {"items": [item.to_dict() for item in items], "count": len(items), "next_cursor": cursor}
    )
