"""有効な短縮URL一覧取得ハンドラー。

API: GET /urls
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """有効な（論理削除されていない）短縮URLの一覧を返す。

    オプションの ``limit`` クエリ文字列パラメータで返却アイテムの最大数を
    制御できる（デフォルト: 50、最大: 200）。

    Args:
        event: API Gatewayプロキシ統合イベント。
        context: Lambdaコンテキスト（未使用）。

    Returns:
        :class:`UrlItem` 辞書のリストを含むAPI Gatewayプロキシレスポンス。
    """
    qs_params: dict[str, str] = event.get("queryStringParameters") or {}

    try:
        limit = min(int(qs_params.get("limit", "50")), 200)
    except (ValueError, TypeError):
        limit = 50

    repo = UrlRepository()
    items = repo.list_active(limit=limit)

    logger.info("有効URL一覧: %d件（limit=%d）", len(items), limit)
    return success_response({
        "items": [item.to_dict() for item in items],
        "count": len(items),
    })
