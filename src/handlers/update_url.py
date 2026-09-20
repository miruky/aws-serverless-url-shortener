"""PATCH /urls/{short_id}: versionによる更新競合の検出。"""

from __future__ import annotations

from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.link_fields import fields
from src.utils.request import api_handler, read_body
from src.utils.response import error_response, success_response
from src.utils.validators import validate_short_id


@api_handler(management=True)
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    short_id = (event.get("pathParameters") or {}).get("short_id", "")
    if not validate_short_id(short_id):
        return error_response("短縮IDが不正です。", 400)
    body = read_body(event)
    version = body.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or not 1 <= version <= 2**53 - 1:
        return error_response("取得時のversionを指定してください。", 400)
    changes = fields(body, partial=True)
    if not changes:
        return error_response("更新するフィールドを指定してください。", 400)
    repo = UrlRepository()
    item = repo.update(short_id, version, changes)
    if item is None:
        return error_response("リンクが変更されています。一覧を更新してやり直してください。", 409)
    return success_response(item.to_dict())
