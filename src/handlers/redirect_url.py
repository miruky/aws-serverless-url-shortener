"""短縮URLリダイレクトハンドラー。

API: GET /{short_id}
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import error_response, redirect_response
from src.utils.validators import validate_short_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """元のURLを検索し、301リダイレクトを返す。

    パスパラメータから ``short_id`` を取得する。短縮URLが存在し有効な場合、
    リダイレクトレスポンスを返す前にクリックカウンターをアトミックにインクリメントする。

    Args:
        event: API Gatewayプロキシ統合イベント。
        context: Lambdaコンテキスト(未使用)。

    Returns:
        API Gatewayプロキシレスポンス(301リダイレクトまたはエラー)。
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("短縮IDが不正です。", 400)

    repo = UrlRepository()
    item = repo.get(short_id)

    if item is None or not item.is_active:
        return error_response("短縮URLが見つかりません。", 404)

    repo.increment_click(short_id)

    logger.info("リダイレクト: %s -> %s", short_id, item.original_url)
    return redirect_response(item.original_url)
