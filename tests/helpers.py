"""管理APIのテストでAPI Gatewayの検証済みコンテキストを再現する。"""

from typing import Any


def admin_event(event: dict[str, Any]) -> dict[str, Any]:
    return {**event, "requestContext": {"authorizer": {"claims": {"sub": "test-owner"}}}}
