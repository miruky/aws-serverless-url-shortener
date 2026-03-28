"""Handler for deleting (soft-delete) a short URL.

API: DELETE /urls/{short_id}
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
    """Soft-delete a short URL so it no longer redirects.

    The item is not physically removed; instead, ``is_active`` is set
    to ``False``.

    Args:
        event: API Gateway proxy integration event.
        context: Lambda context (unused).

    Returns:
        API Gateway proxy response confirming deletion.
    """
    path_params: dict[str, str] = event.get("pathParameters") or {}
    short_id: str = path_params.get("short_id", "")

    if not validate_short_id(short_id):
        return error_response("Invalid short ID.", 400)

    repo = UrlRepository()
    deleted = repo.soft_delete(short_id)

    if not deleted:
        return error_response("Short URL not found.", 404)

    logger.info("Soft-deleted short URL: %s", short_id)
    return success_response({"message": f"Short URL '{short_id}' deleted."})
