"""Handler for redirecting a short URL to its original destination.

API: GET /{short_id}
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import error_response, redirect_response
from src.utils.validators import validate_short_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Look up the original URL and return a 301 redirect.

    The ``short_id`` is extracted from the path parameters.  If the
    short URL is found and active, the click counter is incremented
    atomically before the redirect response is returned.

    Args:
        event: API Gateway proxy integration event.
        context: Lambda context (unused).

    Returns:
        API Gateway proxy response (301 redirect or error).
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("Invalid short ID.", 400)

    repo = UrlRepository()
    item = repo.get(short_id)

    if item is None or not item.is_active:
        return error_response("Short URL not found.", 404)

    repo.increment_click(short_id)

    logger.info("Redirecting %s -> %s", short_id, item.original_url)
    return redirect_response(item.original_url)
