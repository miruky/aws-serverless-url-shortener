"""暗号学的乱数によるID生成。衝突は保存時の条件付き書込で検出する。"""

import secrets
import string

CHARSET = string.ascii_letters + string.digits
DEFAULT_LENGTH = 7


def generate_short_id(url: str, length: int = DEFAULT_LENGTH) -> str:
    """url引数は既存呼出元との互換性のため保持する。"""
    if not isinstance(length, int) or isinstance(length, bool) or not 1 <= length <= 20:
        raise ValueError("length must be between 1 and 20")
    return "".join(secrets.choice(CHARSET) for _ in range(length))
