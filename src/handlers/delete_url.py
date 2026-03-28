"""短縮URL削除(論理削除)ハンドラー。

API: DELETE /urls/{short_id}
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
    """短縮URLを論理削除し、リダイレクトを無効化する。

    アイテムは物理的には削除されず、``is_active`` が ``False`` に設定される。

    Args:
        event: API Gatewayプロキシ統合イベント。
        context: Lambdaコンテキスト(未使用)。

    Returns:
        削除確認のAPI Gatewayプロキシレスポンス。
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("短縮IDが不正です。", 400)

    repo = UrlRepository()
    deleted = repo.soft_delete(short_id)

    if not deleted:
        return error_response("短縮URLが見つかりません。", 404)

    logger.info("短縮URL論理削除: %s", short_id)
    return success_response({"message": f"短縮URL '{short_id}' を削除しました。"})
