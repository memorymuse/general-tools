"""Collector for Claude.ai web export ZIP files."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, Any
import json
import zipfile

from .base import BaseCollector
from ..models import Conversation, Message


class ClaudeWebExportCollector(BaseCollector):
    """
    Collects conversations from Claude.ai export ZIP files.

    Users download exports from Settings > Privacy > Export.
    The ZIP contains JSON files with conversation data.
    """

    source_name = "claude-web"

    def collect(self) -> Iterator[Conversation]:
        """Collect all Claude.ai conversations from inbox ZIP files."""
        if not self.inbox_dir or not self.inbox_dir.exists():
            return

        # Find Claude export ZIPs in inbox (usually named with timestamp)
        for zip_path in self.inbox_dir.glob("*.zip"):
            # Skip ChatGPT exports
            if "chatgpt" in zip_path.name.lower():
                continue

            try:
                yield from self._process_zip(zip_path)
            except Exception as e:
                print(f"Warning: Failed to process {zip_path}: {e}")
                continue

        # Also check for already-extracted JSON files
        for json_path in self.inbox_dir.glob("**/*.json"):
            # Skip known non-conversation files
            if json_path.name in ("users.json", "projects.json", "orgs.json"):
                continue

            # Skip if it looks like a ChatGPT file (unless we're sure it's Claude)
            if "chatgpt" in json_path.name.lower() or "openai" in json_path.parent.name.lower():
                continue

            try:
                # Check if it's a bulk conversations.json (list of conversations)
                if json_path.name == "conversations.json":
                    with open(json_path) as f:
                        # Peek to see if it's a list
                        first_char = f.read(1).strip()
                        if first_char == "[":
                            yield from self._process_bulk_file(json_path)
                            continue

                # Single conversation file
                if self._looks_like_claude_export(json_path):
                    conv = self._parse_conversation_file(json_path)
                    if conv and conv.messages:
                        yield conv
            except Exception as e:
                print(f"Warning: Failed to parse {json_path}: {e}")
                continue

    def _process_bulk_file(self, json_path: Path) -> Iterator[Conversation]:
        """Process a bulk conversations.json file."""
        with open(json_path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            return

        # Pre-scan for attachments in likely locations
        # 1. Same directory
        # 2. Parent directory (common if json is in a subfolder)
        # 3. attachments/ subdirectory
        attachment_dirs = [
            json_path.parent,
            json_path.parent.parent,
            json_path.parent / "attachments",
        ]

        for conv_data in data:
            if self._is_claude_conversation(conv_data):
                # Create a dynamic attachment map for this conversation
                attachment_map = {}
                
                # Scan messages for attachments to find
                for msg in conv_data.get("chat_messages", []):
                    for att in msg.get("attachments", []):
                        file_name = att.get("file_name")
                        if not file_name:
                            continue
                            
                        # Look for file in candidate dirs
                        for d in attachment_dirs:
                            candidate = d / file_name
                            if candidate.exists():
                                # Found it! Archive it.
                                try:
                                    with open(candidate, "rb") as f:
                                        content = f.read()
                                    
                                    archived_path = self._archive_raw(
                                        content,
                                        f"attachments/{file_name}",
                                        extension="",
                                        is_binary=True
                                    )
                                    attachment_map[file_name] = str(archived_path)
                                    break
                                except Exception:
                                    pass

                conv = self._parse_conversation(
                    conv_data, 
                    str(json_path),
                    attachment_map
                )
                if conv and conv.messages:
                    yield conv

    def _process_zip(self, zip_path: Path) -> Iterator[Conversation]:
        """Process a Claude.ai export ZIP file."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            # First pass: Extract all attachments
            attachment_map = {}  # filename -> archived_path
            
            for name in zf.namelist():
                if name.startswith("__") or name.endswith("/"):
                    continue
                    
                # If it's not a JSON file, it's likely an attachment (e.g. in attachments/ folder)
                if not name.endswith(".json"):
                    try:
                        with zf.open(name) as f:
                            content = f.read()
                        
                        # Archive the attachment
                        # Use the original filename (including folder structure if useful)
                        # but flatten slightly for our raw storage
                        safe_name = Path(name).name
                        archived_path = self._archive_raw(
                            content, 
                            f"attachments/{safe_name}", 
                            extension="", # Extension is already in safe_name
                            is_binary=True
                        )
                        attachment_map[safe_name] = str(archived_path)
                    except Exception as e:
                        print(f"Warning: Failed to extract attachment {name}: {e}")

            # Second pass: Process conversations
            for name in zf.namelist():
                if name.endswith(".json") and not name.startswith("__"):
                    try:
                        with zf.open(name) as f:
                            data = json.load(f)

                        # Check if this looks like a Claude conversation
                        if self._is_claude_conversation(data):
                            conv = self._parse_conversation(
                                data, 
                                f"{zip_path}:{name}",
                                attachment_map
                            )
                            if conv and conv.messages:
                                yield conv
                    except Exception as e:
                        print(f"Warning: Failed to parse {name} in {zip_path}: {e}")
                        continue

    def _looks_like_claude_export(self, path: Path) -> bool:
        """Check if a JSON file looks like a Claude.ai export."""
        try:
            with open(path) as f:
                # Just peek at the start
                content = f.read(1000)
                return '"chat_messages"' in content or '"uuid"' in content
        except Exception:
            return False

    def _is_claude_conversation(self, data: Any) -> bool:
        """Check if data looks like a Claude.ai conversation."""
        if not isinstance(data, dict):
            return False
        # Claude exports typically have these fields
        return "uuid" in data or "chat_messages" in data

    def _parse_conversation_file(self, path: Path) -> Conversation | None:
        """Parse a single Claude.ai conversation JSON file."""
        with open(path) as f:
            data = json.load(f)
        return self._parse_conversation(data, str(path))

    def _parse_conversation(
        self, 
        data: dict[str, Any], 
        source_path: str,
        attachment_map: dict[str, str] | None = None
    ) -> Conversation | None:
        """Parse a Claude.ai conversation from export data."""
        native_id = data.get("uuid") or data.get("id")
        if not native_id:
            return None

        # Extract messages
        messages = self._extract_messages(data, attachment_map)
        if not messages:
            return None

        # Extract timestamps
        timestamps = [m.timestamp for m in messages if m.timestamp]
        if timestamps:
            created_at = min(timestamps)
            updated_at = max(timestamps)
        else:
            created_at = datetime.now()
            updated_at = created_at

        # Try to get title
        title = data.get("name") or data.get("title")
        if not title and messages:
            # Generate from first user message
            for msg in messages:
                if msg.role == "user":
                    first_line = msg.content.split("\n")[0].strip()
                    title = first_line[:80] + "..." if len(first_line) > 80 else first_line
                    break

        # Archive raw conversation data
        archived_path = self._archive_raw(data, native_id, "json")

        return Conversation(
            id=f"{self.source_name}:{native_id}",
            source=self.source_name,
            native_id=native_id,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            title=title,
            summary=data.get("summary"),
            metadata={
                "source_path": str(archived_path),
                "original_path": source_path,
                "model": data.get("model"),
                "account_uuid": data.get("account", {}).get("uuid"),
            },
        )

    def _extract_messages(
        self, 
        data: dict[str, Any],
        attachment_map: dict[str, str] | None = None
    ) -> list[Message]:
        """Extract messages from Claude.ai export data."""
        messages: list[Message] = []

        # Claude exports have messages in 'chat_messages' array
        chat_messages = data.get("chat_messages", [])

        for msg_data in chat_messages:
            role = msg_data.get("sender")
            if role == "human":
                role = "user"
            elif role == "assistant":
                role = "assistant"
            else:
                continue

            # Parse content and metadata
            text_parts = []
            metadata = {
                "has_thinking": False,
                "has_tools": False,
                "has_voice": False,
                "tool_calls": [],
                "content_types": [],
                "attachments": [],
            }

            # Capture detailed attachment info
            for att in msg_data.get("attachments", []):
                file_name = att.get("file_name")
                local_path = attachment_map.get(file_name) if attachment_map and file_name else None
                
                metadata["attachments"].append({
                    "file_name": file_name,
                    "file_type": att.get("file_type"),
                    "file_size": att.get("file_size"),
                    "extracted_content": att.get("extracted_content"),
                    "local_path": local_path,  # Link to archived file
                })
            
            metadata["attachment_count"] = len(metadata["attachments"])

            # Handle content array (newer exports)
            content_list = msg_data.get("content", [])
            # Fallback for older exports where 'text' was top-level
            if not content_list and "text" in msg_data:
                content_list = [{"type": "text", "text": msg_data["text"]}]

            for content_item in content_list:
                content_type = content_item.get("type")
                metadata["content_types"].append(content_type)

                if content_type == "text":
                    text_parts.append(content_item.get("text", ""))
                elif content_type == "thinking":
                    metadata["has_thinking"] = True
                    # Store thinking in metadata if needed, or just flag it
                    metadata["thinking_preview"] = content_item.get("thinking", "")[:200]
                elif content_type == "tool_use":
                    metadata["has_tools"] = True
                    metadata["tool_calls"].append({
                        "name": content_item.get("name"),
                        "input": content_item.get("input"),
                        "id": content_item.get("id"),
                    })
                elif content_type == "tool_result":
                    metadata["has_tools"] = True
                elif content_type == "voice_note":
                    metadata["has_voice"] = True

            # Join text parts
            content = "\n".join(text_parts)

            # Fallback if no text content found (e.g. only attachments)
            if not content:
                if metadata["attachment_count"] > 0:
                    content = f"[{metadata['attachment_count']} attachment(s)]"
                elif metadata["has_voice"]:
                    content = "[Voice Note]"
                elif metadata["has_tools"]:
                    content = "[Tool Use]"

            if not content and not metadata["has_tools"]:
                continue

            # Get timestamp
            ts = None
            created_at = msg_data.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    elif isinstance(created_at, (int, float)):
                        ts = datetime.fromtimestamp(created_at)
                except (ValueError, OSError):
                    pass

            messages.append(
                Message(
                    role=role,
                    content=content,
                    timestamp=ts,
                    id=msg_data.get("uuid"),
                    metadata=metadata,
                )
            )

        return messages
