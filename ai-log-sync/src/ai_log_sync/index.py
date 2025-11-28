"""Index management for conversation metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator
import json

from .models import Conversation, IndexEntry


@dataclass
class MergeResult:
    """Result of merging a conversation into the index."""

    action: str  # "added", "updated", "skipped"
    conversation_id: str
    reason: str | None = None


@dataclass
class Index:
    """Manages the conversation index and merge logic."""

    entries: dict[str, IndexEntry] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Index":
        """Load index from a JSON file."""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        entries = {
            entry_data["id"]: IndexEntry.from_dict(entry_data)
            for entry_data in data.get("entries", [])
        }
        return cls(entries=entries)

    def save(self, path: Path) -> None:
        """Save index to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "count": len(self.entries),
            "entries": [entry.to_dict() for entry in self.entries.values()],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def merge(self, conv: Conversation, raw_path: str) -> MergeResult:
        """
        Merge a conversation into the index using "fresher wins" logic.

        Returns:
            MergeResult indicating what action was taken.
        """
        existing = self.entries.get(conv.id)

        if existing is None:
            # New conversation - add it
            self.entries[conv.id] = IndexEntry.from_conversation(conv, raw_path)
            return MergeResult(action="added", conversation_id=conv.id)

        # Existing conversation - compare timestamps
        # Existing conversation - compare timestamps and content
        is_fresher = conv.updated_at > existing.updated_at
        has_more_messages = conv.message_count > existing.message_count
        content_changed = conv.content_hash != existing.content_hash

        if is_fresher or has_more_messages or content_changed:
            # Local is fresher or has new content - update
            self.entries[conv.id] = IndexEntry.from_conversation(conv, raw_path)
            
            reason = []
            if is_fresher:
                reason.append(f"newer timestamp ({conv.updated_at.isoformat()})")
            if has_more_messages:
                reason.append(f"more messages ({conv.message_count} > {existing.message_count})")
            if content_changed and not (is_fresher or has_more_messages):
                reason.append("content changed")
                
            return MergeResult(
                action="updated",
                conversation_id=conv.id,
                reason=", ".join(reason),
            )
        else:
            # Remote is same or fresher - skip
            return MergeResult(
                action="skipped",
                conversation_id=conv.id,
                reason="no changes detected",
            )

    def get(self, conv_id: str) -> IndexEntry | None:
        """Get an entry by ID."""
        return self.entries.get(conv_id)

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[IndexEntry]:
        return iter(self.entries.values())

    def by_source(self, source: str) -> list[IndexEntry]:
        """Get all entries for a specific source."""
        return [e for e in self.entries.values() if e.source == source]

    def stats(self) -> dict[str, int]:
        """Get statistics about the index."""
        by_source: dict[str, int] = {}
        for entry in self.entries.values():
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
        return {
            "total": len(self.entries),
            "by_source": by_source,
        }
