"""公開GET/HEAD /{short_id}: 期限・停止を考慮した一時リダイレクト。"""

from __future__ import annotations

import time
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.request import api_handler
from src.utils.response import error_response, redirect_response
from src.utils.validators import normalize_url, validate_short_id, validate_url


@api_handler(management=False)
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    short_id = (event.get("pathParameters") or {}).get("short_id", "")
    if not validate_short_id(short_id):
        return error_response("短縮IDが不正です。", 400)
    repo = UrlRepository()
    is_head = event.get("httpMethod") == "HEAD"
    item = repo.get(short_id) if is_head else repo.increment_click(short_id)
    if item is None:
        item = repo.get(short_id)
        if item is None or not item.is_active:
            return error_response("短縮URLが見つかりません。", 404)
        if item.expires_at is not None and item.expires_at <= int(time.time()):
            return error_response("このリンクは有効期限を過ぎています。", 410)
        return error_response("リンクの状態が変わりました。再試行してください。", 409)
    if not item.is_active:
        return error_response("短縮URLが見つかりません。", 404)
    if is_head and item.expires_at is not None and item.expires_at <= int(time.time()):
        return error_response("このリンクは有効期限を過ぎています。", 410)
    if not validate_url(item.original_url):
        return error_response("リンク先が利用できません。", 410)
    return redirect_response(normalize_url(item.original_url))
