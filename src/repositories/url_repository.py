"""URLアイテムのDynamoDBリポジトリ。"""

from __future__ import annotations

import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr

from src.models.url import UrlItem

TABLE_NAME: str = os.environ.get("URLS_TABLE_NAME", "urls")


class UrlRepository:
    """URLsテーブルに対するCRUD操作を提供するリポジトリ。

    コンストラクタはオプションで ``dynamodb_resource`` を受け取り、
    依存性注入によりテスト時にモック(例: moto)への差し替えを容易にする。

    Args:
        table_name: DynamoDBテーブル名。
        dynamodb_resource: ``boto3.resource('dynamodb')`` インスタンス。
            ``None`` の場合はデフォルトリソースが生成される。
    """

    def __init__(
        self,
        table_name: str = TABLE_NAME,
        dynamodb_resource: Any = None,
    ) -> None:
        self._dynamodb: Any = dynamodb_resource or boto3.resource("dynamodb")
        self._table: Any = self._dynamodb.Table(table_name)

    # -- 登録 -----------------------------------------------------------------

    def put(self, item: UrlItem) -> None:
        """URLアイテムをテーブルに保存する。

        Args:
            item: 保存する :class:`UrlItem`。
        """
        self._table.put_item(Item=item.to_dict())

    # -- 取得 -----------------------------------------------------------------

    def get(self, short_id: str) -> UrlItem | None:
        """短縮IDでURLアイテムを取得する。

        Args:
            short_id: パーティションキーの値。

        Returns:
            見つかった場合は :class:`UrlItem`、見つからない場合は ``None``。
        """
        response: dict[str, Any] = self._table.get_item(Key={"short_id": short_id})
        data = response.get("Item")
        if data is None:
            return None
        return UrlItem.from_dict(data)

    def list_active(self, limit: int = 50) -> list[UrlItem]:
        """有効な(論理削除されていない)URLアイテムを一覧取得する。

        Args:
            limit: 返却するアイテムの最大数。

        Returns:
            有効な :class:`UrlItem` インスタンスのリスト。
        """
        response: dict[str, Any] = self._table.scan(
            FilterExpression=Attr("is_active").eq(True),
            Limit=limit,
        )
        return [UrlItem.from_dict(item) for item in response.get("Items", [])]

    # -- 更新 -----------------------------------------------------------------

    def increment_click(self, short_id: str) -> None:
        """URLアイテムのクリックカウンターをアトミックにインクリメントする。

        Args:
            short_id: パーティションキーの値。
        """
        self._table.update_item(
            Key={"short_id": short_id},
            UpdateExpression="SET click_count = click_count + :inc",
            ExpressionAttributeValues={":inc": 1},
        )

    # -- 削除(論理削除) -----------------------------------------------------

    def soft_delete(self, short_id: str) -> bool:
        """URLアイテムを論理削除する(``is_active`` を ``False`` に設定)。

        Args:
            short_id: パーティションキーの値。

        Returns:
            アイテムが存在し無効化された場合は ``True``、
            アイテムが見つからなかった場合は ``False``。
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
