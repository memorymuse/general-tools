"""Collector for Claude Code local conversation logs."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, Any
import json

from .base import BaseCollector
from ..models import Conversation, Message


class ClaudeCodeCollector(BaseCollector):
    """
    Collects conversations from Claude Code's local storage.

    Claude Code stores conversations in ~/.claude/projects/<project-hash>/*.jsonl
    Each JSONL file is a session with messages as individual lines.
    """

    source_name = "claude-code"

    def collect(self) -> Iterator[Conversation]:
        """Collect all Claude Code conversations, merging split sessions."""
        from collections import defaultdict

        # Group files by session ID
        session_groups: dict[str, list[Path]] = defaultdict(list)
        
        for base_path in self._expand_paths():
            if not base_path.exists():
                continue

            for project_dir in base_path.iterdir():
                if not project_dir.is_dir():
                    continue

                for jsonl_file in project_dir.glob("*.jsonl"):
                    try:
                        session_id = self._get_session_id(jsonl_file)
                        if session_id:
                            session_groups[session_id].append(jsonl_file)
                    except Exception as e:
                        print(f"Warning: Failed to scan {jsonl_file}: {e}")
                        continue

        # Process each group
        for session_id, files in session_groups.items():
            try:
                all_messages: list[Message] = []
                archived_paths: list[str] = []
                timestamps: list[datetime] = []
                project_path: str | None = None

                for jsonl_file in files:
                    # Archive raw file
                    with open(jsonl_file, "r") as f:
                        content = f.read()
                    
                    # Use filename as ID for archival to preserve all fragments
                    archived = self._archive_raw(content, jsonl_file.stem, "jsonl")
                    archived_paths.append(str(archived))

                    # Parse session fragment
                    fragment = self._parse_session_fragment(jsonl_file)
                    if fragment:
                        all_messages.extend(fragment["messages"])
                        timestamps.extend(fragment["timestamps"])
                        if not project_path and fragment["project_path"]:
                            project_path = fragment["project_path"]

                if not all_messages:
                    continue

                # Deduplicate and sort messages
                messages = self._deduplicate_messages(all_messages)
                
                # Determine timestamps
                if timestamps:
                    created_at = min(timestamps)
                    updated_at = max(timestamps)
                else:
                    created_at = datetime.now()
                    updated_at = created_at

                # Use the main session ID
                native_id = session_id

                yield Conversation(
                    id=f"{self.source_name}:{native_id}",
                    source=self.source_name,
                    native_id=native_id,
                    created_at=created_at,
                    updated_at=updated_at,
                    messages=messages,
                    title=self._generate_title(messages, project_path),
                    metadata={
                        "project_path": project_path,
                        "source_path": archived_paths[0] if archived_paths else None,
                        "all_source_paths": archived_paths,
                        "fragment_count": len(files),
                    },
                )

            except Exception as e:
                print(f"Warning: Failed to process session {session_id}: {e}")
                continue

    def _get_session_id(self, jsonl_path: Path) -> str | None:
        """Extract session ID from a JSONL file."""
        # First, try to find sessionId in the first 100 lines
        with open(jsonl_path) as f:
            try:
                for _ in range(100):
                    line = f.readline()
                    if not line:
                        break
                    try:
                        entry = json.loads(line)
                        if "sessionId" in entry:
                            return entry["sessionId"]
                    except json.JSONDecodeError:
                        continue
            except OSError:
                pass

        # Fallback: Check if filename is a UUID
        # Simple heuristic: 36 chars, dashes at 8, 13, 18, 23
        stem = jsonl_path.stem
        if len(stem) == 36 and stem.count("-") == 4:
            return stem
            
        return None

    def _parse_session_fragment(self, jsonl_path: Path) -> dict[str, Any] | None:
        """Parse a single JSONL file into messages and metadata."""
        messages: list[Message] = []
        timestamps: list[datetime] = []
        project_path: str | None = None

        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if project_path is None:
                    project_path = entry.get("cwd")

                ts = self._parse_timestamp(entry)
                if ts:
                    timestamps.append(ts)

                msg = self._extract_message(entry)
                if msg:
                    messages.append(msg)

        if not messages:
            return None

        return {
            "messages": messages,
            "timestamps": timestamps,
            "project_path": project_path,
        }

    def _deduplicate_messages(self, messages: list[Message]) -> list[Message]:
        """Deduplicate messages based on content and timestamp."""
        unique_msgs = {}
        
        for msg in messages:
            # Create a unique key for the message
            # Use timestamp (if available), role, and content hash
            ts_str = msg.timestamp.isoformat() if msg.timestamp else "None"
            key = (ts_str, msg.role, hash(msg.content))
            
            if key not in unique_msgs:
                unique_msgs[key] = msg
        
        # Sort by timestamp
        return sorted(
            unique_msgs.values(), 
            key=lambda m: m.timestamp or datetime.min
        )

    def _parse_timestamp(self, entry: dict[str, Any]) -> datetime | None:
        """Extract timestamp from a JSONL entry."""
        # Try ISO format first
        ts_str = entry.get("timestamp")
        if isinstance(ts_str, str):
            try:
                return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Try Unix timestamp (milliseconds)
        if isinstance(ts_str, (int, float)):
            try:
                return datetime.fromtimestamp(ts_str / 1000)
            except (ValueError, OSError):
                pass

        return None

    def _extract_message(self, entry: dict[str, Any]) -> Message | None:
        """Extract a message from a JSONL entry."""
        entry_type = entry.get("type")

        # Skip non-message entries
        if entry_type not in ("user", "assistant"):
            return None

        # Get message content
        message_data = entry.get("message", {})
        content_parts = message_data.get("content", [])

        # Metadata initialization
        metadata = {
            "has_tools": False,
            "tool_calls": [],
            "model": message_data.get("model"),
            "usage": message_data.get("usage", {}),
        }

        # Handle different content structures
        if isinstance(content_parts, str):
            text = content_parts
        elif isinstance(content_parts, list):
            # Extract text from content blocks
            text_parts = []
            for part in content_parts:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif part.get("type") == "tool_use":
                        metadata["has_tools"] = True
                        metadata["tool_calls"].append({
                            "name": part.get("name"),
                            "input": part.get("input"),
                            "id": part.get("id"),
                        })
                        # Include tool marker in text
                        text_parts.append(f"[Tool Use: {part.get('name')}]")
                    elif part.get("type") == "tool_result":
                        metadata["has_tools"] = True
                        # Optionally include result marker
                        # text_parts.append(f"[Tool Result]")

            text = "\n".join(text_parts)
        else:
            return None

        if not text.strip() and not metadata["has_tools"]:
            return None

        # Get timestamp
        ts = self._parse_timestamp(entry)

        return Message(
            role=entry_type,
            content=text,
            timestamp=ts,
            id=entry.get("uuid"),  # Some Claude Code entries might have UUIDs
            metadata=metadata,
        )

    def _generate_title(
        self, messages: list[Message], project_path: str | None
    ) -> str | None:
        """Generate a title from the first user message or project path."""
        # Try first user message
        for msg in messages:
            if msg.role == "user" and msg.content:
                # Take first line, truncate to 80 chars
                first_line = msg.content.split("\n")[0].strip()
                if len(first_line) > 80:
                    return first_line[:77] + "..."
                return first_line

        # Fallback to project name
        if project_path:
            return Path(project_path).name

        return None
