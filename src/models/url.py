"""URL model definitions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class UrlItem:
    """Represents a shortened URL entry stored in DynamoDB.

    Attributes:
        short_id: Unique short identifier (e.g. 'aB3kZ9x').
        original_url: The original long URL to redirect to.
        created_at: Unix timestamp of creation (auto-set).
        click_count: Number of redirect accesses.
        is_active: Soft-delete flag.
    """

    short_id: str
    original_url: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    click_count: int = 0
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to a DynamoDB-compatible dictionary."""
        return {
            "short_id": self.short_id,
            "original_url": self.original_url,
            "created_at": self.created_at,
            "click_count": self.click_count,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UrlItem:
        """Create a UrlItem from a DynamoDB item dictionary.

        Missing optional fields fall back to safe defaults so that items
        written by older schema versions can still be loaded.
        """
        return cls(
            short_id=str(data["short_id"]),
            original_url=str(data["original_url"]),
            created_at=int(data.get("created_at", 0)),
            click_count=int(data.get("click_count", 0)),
            is_active=bool(data.get("is_active", True)),
        )
