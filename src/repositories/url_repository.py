"""条件付き書込とページングを提供するDynamoDBデータ層。"""

from __future__ import annotations

import base64
import binascii
import json
import os
import time
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, ConditionBase

from src.models.url import UrlItem
from src.utils.validators import validate_short_id


class IdConflictError(Exception):
    """短縮IDが使用済み。停止済みIDも再利用しない。"""


class UrlRepository:
    def __init__(self, table_name: str | None = None, dynamodb_resource: Any = None) -> None:
        self._dynamodb: Any = dynamodb_resource or boto3.resource("dynamodb")
        self._table: Any = self._dynamodb.Table(
            table_name or os.environ.get("URLS_TABLE_NAME", "urls")
        )

    def put(self, item: UrlItem) -> None:
        try:
            self._table.put_item(
                Item=item.to_dict(), ConditionExpression=Attr("short_id").not_exists()
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException as exc:
            raise IdConflictError from exc

    def get(self, short_id: str) -> UrlItem | None:
        response = self._table.get_item(Key={"short_id": short_id}, ConsistentRead=True)
        return UrlItem.from_dict(response["Item"]) if "Item" in response else None

    def list_page(
        self, limit: int = 50, cursor: str | None = None
    ) -> tuple[list[UrlItem], str | None]:
        if not 1 <= limit <= 200:
            raise ValueError("limitは1〜200です。")
        kwargs: dict[str, Any] = {"Limit": limit}
        if cursor:
            try:
                if len(cursor) > 256:
                    raise ValueError
                key = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
                if (
                    not isinstance(key, dict)
                    or set(key) != {"short_id"}
                    or not validate_short_id(key["short_id"])
                ):
                    raise ValueError
                kwargs["ExclusiveStartKey"] = key
            except (ValueError, binascii.Error, UnicodeError) as exc:
                raise ValueError("ページ指定が不正です。") from exc
        response = self._table.scan(**kwargs)
        next_key = response.get("LastEvaluatedKey")
        token = (
            base64.urlsafe_b64encode(json.dumps(next_key).encode()).decode() if next_key else None
        )
        return [UrlItem.from_dict(item) for item in response.get("Items", [])], token

    def list_active(self, limit: int = 50) -> list[UrlItem]:
        """既存内部呼出元用。公開APIはlist_pageの継続トークンを使用する。"""
        if not 1 <= limit <= 200:
            raise ValueError("limitは1〜200です。")
        paginator = self._table.meta.client.get_paginator("scan")
        items: list[UrlItem] = []
        for page in paginator.paginate(
            TableName=self._table.name,
            FilterExpression=Attr("is_active").eq(True),
            PaginationConfig={"PageSize": limit},
        ):
            items.extend(UrlItem.from_dict(item) for item in page.get("Items", []))
            if len(items) >= limit:
                break
        return items[:limit]

    def increment_click(self, short_id: str) -> UrlItem | None:
        """停止と期限を更新と同時に判定し、更新時点の転送先を返す。"""
        try:
            response = self._table.update_item(
                Key={"short_id": short_id},
                UpdateExpression="SET click_count = if_not_exists(click_count, :zero) + :one",
                ExpressionAttributeValues={":zero": 0, ":one": 1},
                ConditionExpression=Attr("short_id").exists()
                & (Attr("is_active").not_exists() | Attr("is_active").eq(True))
                & (Attr("expires_at").not_exists() | Attr("expires_at").gt(int(time.time()))),
                ReturnValues="ALL_NEW",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        return UrlItem.from_dict(response["Attributes"])

    def soft_delete(self, short_id: str) -> bool:
        try:
            self._table.update_item(
                Key={"short_id": short_id},
                UpdateExpression=(
                    "SET is_active = :val, #version = if_not_exists(#version, :one) + :one"
                ),
                ExpressionAttributeNames={"#version": "version"},
                ExpressionAttributeValues={":val": False, ":one": 1},
                ConditionExpression=Attr("short_id").exists(),
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    def update(self, short_id: str, version: int, changes: dict[str, Any]) -> UrlItem | None:
        assignments = ["#version = if_not_exists(#version, :one) + :one"]
        names = {"#version": "version"}
        values: dict[str, Any] = {":one": 1}
        remove = []
        for key, value in changes.items():
            if key not in {"title", "original_url", "expires_at", "is_active"}:
                raise ValueError("更新できないフィールドです。")
            names[f"#{key}"] = key
            if value is None:
                remove.append(f"#{key}")
            else:
                values[f":{key}"] = value
                assignments.append(f"#{key} = :{key}")
        condition: ConditionBase = Attr("version").eq(version)
        if version == 1:
            condition = condition | Attr("version").not_exists()
        try:
            response = self._table.update_item(
                Key={"short_id": short_id},
                UpdateExpression="SET "
                + ", ".join(assignments)
                + (" REMOVE " + ", ".join(remove) if remove else ""),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression=Attr("short_id").exists() & condition,
                ReturnValues="ALL_NEW",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return None
        return UrlItem.from_dict(response["Attributes"])
