"""Short ID generation utilities."""

from __future__ import annotations

import hashlib
import string
import time

CHARSET: str = string.ascii_letters + string.digits  # a-zA-Z0-9 (62 chars)
DEFAULT_LENGTH: int = 7


def generate_short_id(url: str, length: int = DEFAULT_LENGTH) -> str:
    """Generate a unique short ID from a URL.

    Uses SHA-256 hash of the URL combined with a nanosecond timestamp to
    produce a collision-resistant, URL-safe identifier.

    Args:
        url: The original URL to derive the short ID from.
        length: Desired length of the short ID (default: 7).

    Returns:
        A string of ``length`` characters from ``[a-zA-Z0-9]``.
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
