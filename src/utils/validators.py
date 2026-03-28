"""入力バリデーションユーティリティ。"""

from __future__ import annotations

import re

URL_PATTERN: re.Pattern[str] = re.compile(
    r"^https?://"
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}"
    r"(?::\d{1,5})?"
    r"(?:/[^\s]*)?$"
)

SHORT_ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9]{1,20}$")


def validate_url(url: str) -> bool:
    """URLが正しい形式のHTTPまたはHTTPS URLかを検証する。

    Args:
        url: 検証する文字列。

    Returns:
        有効なURLなら ``True``、そうでなければ ``False``。
    """
    if not url or not isinstance(url, str):
        return False
    if len(url) > 2048:
        return False
    return bool(URL_PATTERN.match(url))


def validate_short_id(short_id: str) -> bool:
    """短縮IDが正しい形式かを検証する。

    有効な短縮IDは1〜20文字の英数字で構成される。

    Args:
        short_id: 検証する文字列。

    Returns:
        有効なら ``True``、そうでなければ ``False``。
    """
    if not short_id or not isinstance(short_id, str):
        return False
    return bool(SHORT_ID_PATTERN.match(short_id))
