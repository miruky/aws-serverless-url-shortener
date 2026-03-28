"""Handler for retrieving statistics of a short URL.

API: GET /urls/{short_id}
"""

from __future__ import annotations

import logging
from typing import Any

from src.repositories.url_repository import UrlRepository
from src.utils.response import error_response, success_response
from src.utils.validators import validate_short_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return the metadata and click statistics for a short URL.

    Args:
        event: API Gateway proxy integration event.
        context: Lambda context (unused).

    Returns:
        API Gateway proxy response containing :class:`UrlItem` data.
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("Invalid short ID.", 400)

    repo = UrlRepository()
    item = repo.get(short_id)

    if item is None:
        return error_response("Short URL not found.", 404)

    logger.info("Stats requested for %s", short_id)
    return success_response(item.to_dict())
