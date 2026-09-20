"""URLの構文検査。DNS解決やリンク先の安全性判定は行わない。"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import quote, urlsplit, urlunsplit

SHORT_ID_PATTERN = re.compile(r"[a-zA-Z0-9]{1,20}")
RESERVED_IDS = {"urls", "app", "health", "docs", "api", "robots", "favicon", "admin"}


def validate_url(url: str) -> bool:
    if not isinstance(url, str) or not url or len(url) > 2048:
        return False
    if any(ord(c) < 33 or ord(c) == 127 for c in url) or "\\" in url:
        return False
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            return False
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
        try:
            return ipaddress.ip_address(hostname).is_global
        except ValueError:
            pass
        if hostname.endswith((".local", ".internal", ".localhost")):
            return False
        labels = hostname.split(".")
        return (
            len(hostname) <= 253
            and len(labels) >= 2
            and all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", s) for s in labels)
            and not labels[-1].isdigit()
        )
    except (ValueError, UnicodeError):
        return False


def validate_short_id(short_id: str) -> bool:
    return isinstance(short_id, str) and SHORT_ID_PATTERN.fullmatch(short_id) is not None


def available_alias(short_id: str) -> bool:
    return validate_short_id(short_id) and short_id.lower() not in RESERVED_IDS


def normalize_url(url: str) -> str:
    """検証済みIRIをHTTP Locationに使えるASCIIのURIへ変換する。"""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").encode("idna").decode("ascii")
    if ":" in host:
        host = f"[{host}]"
    if parsed.port is not None:
        host += f":{parsed.port}"
    safe = "/?:@!$&'()*+,;=-._~%"
    return urlunsplit(
        (
            parsed.scheme,
            host,
            quote(parsed.path, safe=safe),
            quote(parsed.query, safe=safe),
            quote(parsed.fragment, safe=safe),
        )
    )
