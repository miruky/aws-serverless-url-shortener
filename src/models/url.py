"""URLモデル定義。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UrlItem:
    """DynamoDBに保存される短縮URLエントリを表すデータクラス。

    Attributes:
        short_id: 一意の短縮ID（例: 'aB3kZ9x'）。
        original_url: リダイレクト先の元のURL。
        created_at: 作成時のUnixタイムスタンプ（自動設定）。
        click_count: リダイレクトアクセス回数。
        is_active: 論理削除フラグ。
    """

    short_id: str
    original_url: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    click_count: int = 0
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """DynamoDB互換の辞書に変換する。"""
        return {
            "short_id": self.short_id,
            "original_url": self.original_url,
            "created_at": self.created_at,
            "click_count": self.click_count,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UrlItem:
        """DynamoDBアイテム辞書からUrlItemを生成する。

        省略されたオプションフィールドは安全なデフォルト値にフォールバックするため、
        旧スキーマバージョンのアイテムも読み込み可能。
        """
        return cls(
            short_id=str(data["short_id"]),
            original_url=str(data["original_url"]),
            created_at=int(data.get("created_at", 0)),
            click_count=int(data.get("click_count", 0)),
            is_active=bool(data.get("is_active", True)),
        )
