"""リンク作成・更新で共通のフィールド検査。"""

from __future__ import annotations

import time
from typing import Any

from src.utils.validators import normalize_url, validate_url


def fields(body: dict[str, Any], *, partial: bool = False) -> dict[str, Any]:
    allowed = (
        {"url", "title", "expires_at", "is_active", "version"}
        if partial
        else {"url", "title", "expires_at", "custom_alias"}
    )
    if set(body) - allowed:
        raise ValueError("未対応のフィールドがあります。")
    result: dict[str, Any] = {}
    if "url" in body or not partial:
        if not validate_url(body.get("url", "")):
            raise ValueError("公開HTTP(S) URLを入力してください。")
        result["original_url"] = normalize_url(body["url"])
    if "title" in body or not partial:
        title = body.get("title", "")
        if not isinstance(title, str) or len(title) > 120 or any(ord(c) < 32 for c in title):
            raise ValueError("タイトルは改行を含まない120文字以内の文字列です。")
        result["title"] = title.strip()
    if "expires_at" in body:
        expiry = body["expires_at"]
        if expiry is not None and (
            not isinstance(expiry, int)
            or isinstance(expiry, bool)
            or not int(time.time()) < expiry <= 253402300799
        ):
            raise ValueError("有効期限には未来のUnix秒を指定してください。")
        result["expires_at"] = expiry
    if "is_active" in body:
        if not isinstance(body["is_active"], bool):
            raise ValueError("is_activeは真偽値です。")
        result["is_active"] = body["is_active"]
    return result
