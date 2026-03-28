"""短縮URL統計情報取得ハンドラー。

API: GET /urls/{short_id}
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import error_response, success_response
from src.utils.validators import validate_short_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """短縮URLのメタデータとクリック統計を返す。

    Args:
        event: API Gatewayプロキシ統合イベント。
        context: Lambdaコンテキスト（未使用）。

    Returns:
        :class:`UrlItem` データを含むAPI Gatewayプロキシレスポンス。
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("短縮IDが不正です。", 400)

    repo = UrlRepository()
    item = repo.get(short_id)

    if item is None:
        return error_response("短縮URLが見つかりません。", 404)

    logger.info("統計情報取得: %s", short_id)
    return success_response(item.to_dict())
