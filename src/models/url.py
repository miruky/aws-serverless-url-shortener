"""旧レコードの読込互換性を保つリンクモデル。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UrlItem:
    short_id: str
    original_url: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    click_count: int = 0
    is_active: bool = True
    title: str = ""
    expires_at: int | None = None
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "short_id": self.short_id,
            "original_url": self.original_url,
            "created_at": self.created_at,
            "click_count": self.click_count,
            "is_active": self.is_active,
            "title": self.title,
            "version": self.version,
        }
        if self.expires_at is not None:
            data["expires_at"] = self.expires_at
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UrlItem:
        return cls(
            short_id=str(data["short_id"]),
            original_url=str(data["original_url"]),
            created_at=int(data.get("created_at", 0)),
            click_count=int(data.get("click_count", 0)),
            is_active=bool(data.get("is_active", True)),
            title=str(data.get("title", "")),
            expires_at=int(data["expires_at"]) if data.get("expires_at") is not None else None,
            version=int(data.get("version", 1)),
        )
