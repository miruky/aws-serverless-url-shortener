"""Handler for creating a shortened URL.

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
    """Create a new short URL entry.

    Expects a JSON body with a ``url`` field containing a valid HTTP(S) URL.
    Returns a ``201 Created`` response with the persisted :class:`UrlItem`.

    Args:
        event: API Gateway proxy integration event.
        context: Lambda context (unused).

    Returns:
        API Gateway proxy response.
    """
    try:
        body: dict[str, Any] = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return error_response("Invalid JSON in request body.", 400)

    original_url: str = body.get("url", "")
    if not validate_url(original_url):
        return error_response("Invalid or missing 'url' parameter.", 400)

    short_id = generate_short_id(original_url)
    item = UrlItem(short_id=short_id, original_url=original_url)

    repo = UrlRepository()
    repo.put(item)

    logger.info("Created short URL: %s -> %s", short_id, original_url)
    return success_response(item.to_dict(), 201)
