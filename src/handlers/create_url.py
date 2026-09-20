"""POST /urls: 認証済み管理者がリンクを作成する。"""

from __future__ import annotations

import os
from typing import Any

from src.models.url import UrlItem
from src.repositories.url_repository import IdConflictError, UrlRepository
from src.utils.link_fields import fields
from src.utils.request import api_handler, read_body
from src.utils.response import error_response, success_response
from src.utils.short_id import generate_short_id
from src.utils.validators import available_alias


@api_handler(management=True)
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    body = read_body(event)
    data = fields(body)
    alias = body.get("custom_alias")
    if alias is not None and not available_alias(alias):
        return error_response("短縮IDは予約語を除く1〜20文字の英数字にしてください。", 400)
    repo = UrlRepository()
    for _ in range(5):
        short_id = alias or generate_short_id(data["original_url"])
        if not available_alias(short_id):
            continue
        item = UrlItem(short_id=short_id, **data)
        try:
            repo.put(item)
        except IdConflictError:
            if alias:
                return error_response("この短縮IDは使用済みです。", 409)
            continue
        result = item.to_dict()
        base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
        if base:
            result["short_url"] = f"{base}/{short_id}"
        return success_response(result, 201)
    return error_response("短縮IDを確保できませんでした。再試行してください。", 503)
