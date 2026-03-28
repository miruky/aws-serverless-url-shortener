"""Input validation utilities."""

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
    """Validate that *url* is a well-formed HTTP or HTTPS URL.

    Args:
        url: The string to validate.

    Returns:
        ``True`` if the string is a valid URL, ``False`` otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    if len(url) > 2048:
        return False
    return bool(URL_PATTERN.match(url))


def validate_short_id(short_id: str) -> bool:
    """Validate that *short_id* is a well-formed short identifier.

    A valid short ID consists of 1–20 alphanumeric characters.

    Args:
        short_id: The string to validate.

    Returns:
        ``True`` if valid, ``False`` otherwise.
    """
    if not short_id or not isinstance(short_id, str):
        return False
    return bool(SHORT_ID_PATTERN.match(short_id))
