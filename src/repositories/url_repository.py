"""DynamoDB repository for URL items."""

from __future__ import annotations

import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr

from src.models.url import UrlItem

TABLE_NAME: str = os.environ.get("URLS_TABLE_NAME", "urls")


class UrlRepository:
    """Repository providing CRUD operations for the URLs DynamoDB table.

    The constructor accepts an optional ``dynamodb_resource`` for
    dependency injection, making it straightforward to swap in a mock
    (e.g. *moto*) during testing.

    Args:
        table_name: Name of the DynamoDB table.
        dynamodb_resource: A ``boto3.resource('dynamodb')`` instance.
            When ``None`` a default resource is created.
    """

    def __init__(
        self,
        table_name: str = TABLE_NAME,
        dynamodb_resource: Any = None,
    ) -> None:
        self._dynamodb: Any = dynamodb_resource or boto3.resource("dynamodb")
        self._table: Any = self._dynamodb.Table(table_name)

    # -- Create ---------------------------------------------------------------

    def put(self, item: UrlItem) -> None:
        """Store a URL item in the table.

        Args:
            item: The :class:`UrlItem` to persist.
        """
        self._table.put_item(Item=item.to_dict())

    # -- Read -----------------------------------------------------------------

    def get(self, short_id: str) -> UrlItem | None:
        """Retrieve a URL item by *short_id*.

        Args:
            short_id: The partition key value.

        Returns:
            A :class:`UrlItem` if found, otherwise ``None``.
        """
        response: dict[str, Any] = self._table.get_item(Key={"short_id": short_id})
        data = response.get("Item")
        if data is None:
            return None
        return UrlItem.from_dict(data)

    def list_active(self, limit: int = 50) -> list[UrlItem]:
        """List active (non-deleted) URL items.

        Args:
            limit: Maximum number of items to return.

        Returns:
            A list of active :class:`UrlItem` instances.
        """
        response: dict[str, Any] = self._table.scan(
            FilterExpression=Attr("is_active").eq(True),
            Limit=limit,
        )
        return [UrlItem.from_dict(item) for item in response.get("Items", [])]

    # -- Update ---------------------------------------------------------------

    def increment_click(self, short_id: str) -> None:
        """Atomically increment the click counter for a URL item.

        Args:
            short_id: The partition key value.
        """
        self._table.update_item(
            Key={"short_id": short_id},
            UpdateExpression="SET click_count = click_count + :inc",
            ExpressionAttributeValues={":inc": 1},
        )

    # -- Delete (soft) --------------------------------------------------------

    def soft_delete(self, short_id: str) -> bool:
        """Soft-delete a URL item by setting ``is_active`` to ``False``.

        Args:
            short_id: The partition key value.

        Returns:
            ``True`` if the item existed and was deactivated,
            ``False`` if the item was not found.
        """
        try:
            self._table.update_item(
                Key={"short_id": short_id},
                UpdateExpression="SET is_active = :val",
                ExpressionAttributeValues={":val": False},
                ConditionExpression=Attr("short_id").exists(),
            )
        except self._dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True
