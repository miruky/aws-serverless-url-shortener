"""Handler for listing all active short URLs.

API: GET /urls
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import success_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return a list of all active (non-deleted) short URLs.

    An optional ``limit`` query-string parameter controls the maximum
    number of items returned (default 50, max 200).

    Args:
        event: API Gateway proxy integration event.
        context: Lambda context (unused).

    Returns:
        API Gateway proxy response with a list of :class:`UrlItem` dicts.
    """
    qs_params: dict[str, str] = event.get("queryStringParameters") or {}

    try:
        limit = min(int(qs_params.get("limit", "50")), 200)
    except (ValueError, TypeError):
        limit = 50

    repo = UrlRepository()
    items = repo.list_active(limit=limit)

    logger.info("Listed %d active URLs (limit=%d)", len(items), limit)
    return success_response({
        "items": [item.to_dict() for item in items],
        "count": len(items),
    })
