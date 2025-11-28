"""Data models for normalized conversation logs."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import hashlib
import json


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime | None = None
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=ts,
            id=data.get("id"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "id": self.id,
            "metadata": self.metadata,
        }


@dataclass
class Conversation:
    """A normalized conversation from any source."""

    id: str  # Canonical ID: "{source}:{native_id}"
    source: str  # Platform identifier (claude-code, chatgpt, etc.)
    native_id: str  # Platform's original ID
    updated_at: datetime  # Last message timestamp
    created_at: datetime  # First message timestamp
    messages: list[Message] = field(default_factory=list)
    title: str | None = None  # Conversation title if available
    summary: str | None = None  # Auto-generated summary if available
    metadata: dict[str, Any] = field(default_factory=dict)  # Platform-specific metadata

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def content_hash(self) -> str:
        """Generate SHA256 hash of conversation content for integrity verification."""
        content = json.dumps(
            [m.to_dict() for m in self.messages],
            sort_keys=True,
            default=str,
        )
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        """Create a Conversation from a dictionary."""
        updated_at = data["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            source=data["source"],
            native_id=data["native_id"],
            updated_at=updated_at,
            created_at=created_at,
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            title=data.get("title"),
            summary=data.get("summary"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source,
            "native_id": self.native_id,
            "updated_at": self.updated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "title": self.title,
            "summary": self.summary,
            "message_count": self.message_count,
            "content_hash": self.content_hash,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
        }


@dataclass
class IndexEntry:
    """Entry in the index.json file (metadata only, no messages)."""

    id: str
    source: str
    native_id: str
    updated_at: datetime
    created_at: datetime
    title: str | None
    message_count: int
    content_hash: str
    raw_path: str  # Path to full conversation file

    @classmethod
    def from_conversation(cls, conv: Conversation, raw_path: str) -> "IndexEntry":
        """Create an index entry from a conversation."""
        return cls(
            id=conv.id,
            source=conv.source,
            native_id=conv.native_id,
            updated_at=conv.updated_at,
            created_at=conv.created_at,
            title=conv.title,
            message_count=conv.message_count,
            content_hash=conv.content_hash,
            raw_path=raw_path,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexEntry":
        updated_at = data["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        created_at = data["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            source=data["source"],
            native_id=data["native_id"],
            updated_at=updated_at,
            created_at=created_at,
            title=data.get("title"),
            message_count=data["message_count"],
            content_hash=data["content_hash"],
            raw_path=data["raw_path"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "native_id": self.native_id,
            "updated_at": self.updated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "title": self.title,
            "message_count": self.message_count,
            "content_hash": self.content_hash,
            "raw_path": self.raw_path,
        }
