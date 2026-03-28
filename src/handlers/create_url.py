"""短縮URL作成ハンドラー。

API: POST /urls
Body: {"url": "https://example.com/very/long/path"}
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.models.url import UrlItem
from src.repositories.url_repository import UrlRepository
from src.utils.response import error_response, success_response
from src.utils.short_id import generate_short_id
from src.utils.validators import validate_url

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """新しい短縮URLエントリを作成する。

    有効なHTTP(S) URLを含む ``url`` フィールドのJSONボディを期待する。
    永続化された :class:`UrlItem` を含む ``201 Created`` レスポンスを返す。

    Args:
        event: API Gatewayプロキシ統合イベント。
        context: Lambdaコンテキスト(未使用)。

    Returns:
        API Gatewayプロキシレスポンス。
    """
    try:
        body: dict[str, Any] = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return error_response("リクエストボディのJSONが不正です。", 400)

    original_url: str = body.get("url", "")
    if not validate_url(original_url):
        return error_response("'url' パラメータが不正または未指定です。", 400)

    short_id = generate_short_id(original_url)
    item = UrlItem(short_id=short_id, original_url=original_url)

    repo = UrlRepository()
    repo.put(item)

    logger.info("短縮URL作成: %s -> %s", short_id, original_url)
    return success_response(item.to_dict(), 201)
