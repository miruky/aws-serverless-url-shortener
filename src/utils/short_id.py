"""短縮ID生成ユーティリティ。"""

from __future__ import annotations

import hashlib
import string
import time

CHARSET: str = string.ascii_letters + string.digits  # a-zA-Z0-9(62文字)
DEFAULT_LENGTH: int = 7


def generate_short_id(url: str, length: int = DEFAULT_LENGTH) -> str:
    """URLから一意の短縮IDを生成する。

    URLとナノ秒タイムスタンプを組み合わせたSHA-256ハッシュにより、
    衝突耐性の高いURL安全な識別子を生成する。

    Args:
        url: 短縮IDの生成元となるURL。
        length: 短縮IDの文字数(デフォルト: 7)。

    Returns:
        ``[a-zA-Z0-9]`` から構成される ``length`` 文字の文字列。
    """
    raw = f"{url}:{time.time_ns()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()

    num = int(digest[:16], 16)
    chars: list[str] = []
    base = len(CHARSET)

    while num and len(chars) < length:
        num, remainder = divmod(num, base)
        chars.append(CHARSET[remainder])

    return "".join(chars).ljust(length, "a")[:length]
