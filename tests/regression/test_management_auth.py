"""匿名リクエストはデータ層へ到達しない。"""

import json
from importlib import import_module
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.parametrize("name", ["create_url", "delete_url", "get_url_stats", "list_urls"])
def test_anonymous_management_is_rejected_before_storage(name):
    module = import_module(f"src.handlers.{name}")
    repository = MagicMock()
    repository.list_active.return_value = []
    repository.get.return_value = None
    request = {
        "body": json.dumps({"url": "https://example.com"}),
        "pathParameters": {"short_id": "abc"},
    }
    with patch.object(module, "UrlRepository", return_value=repository) as factory:
        response = module.handler(request, None)
        assert response["statusCode"] == 401
        factory.assert_not_called()
