"""Collector for ChatGPT web export ZIP files."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterator, Any
import json
import zipfile

from .base import BaseCollector
from ..models import Conversation, Message


class ChatGPTExportCollector(BaseCollector):
    """
    Collects conversations from ChatGPT export ZIP files.

    Users download exports from Settings > Data Controls > Export.
    The ZIP contains conversations.json with all conversations.
    """

    source_name = "chatgpt"

    def collect(self) -> Iterator[Conversation]:
        """Collect all ChatGPT conversations from inbox ZIP files."""
        if not self.inbox_dir or not self.inbox_dir.exists():
            return

        # Find ChatGPT export ZIPs in inbox
        for zip_path in self.inbox_dir.glob("*chatgpt*.zip"):
            try:
                yield from self._process_zip(zip_path)
            except Exception as e:
                print(f"Warning: Failed to process {zip_path}: {e}")
                continue

        # Also check for already-extracted conversations.json
        for json_path in self.inbox_dir.glob("**/conversations.json"):
            # Skip if it looks like a non-ChatGPT file
            parent_name = json_path.parent.name.lower()
            if "chatgpt" in parent_name or "openai" in parent_name or parent_name == "inbox":
                try:
                    yield from self._parse_conversations_file(json_path)
                except Exception as e:
                    print(f"Warning: Failed to parse {json_path}: {e}")
                    continue

    def _process_zip(self, zip_path: Path) -> Iterator[Conversation]:
        """Process a ChatGPT export ZIP file."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Look for conversations.json
            for name in zf.namelist():
                if name.endswith("conversations.json"):
                    with zf.open(name) as f:
                        data = json.load(f)
                        yield from self._parse_conversations(data, str(zip_path))
                    break

    def _parse_conversations_file(self, path: Path) -> Iterator[Conversation]:
        """Parse a conversations.json file directly."""
        with open(path) as f:
            data = json.load(f)
        
        # Pass the parent directory to find attachments
        yield from self._parse_conversations(data, str(path), attachment_root=path.parent)

    def _parse_conversations(
        self, 
        data: list[dict[str, Any]], 
        source_path: str,
        attachment_root: Path | None = None
    ) -> Iterator[Conversation]:
        """Parse conversations from ChatGPT export data."""
        for conv_data in data:
            try:
                conv = self._parse_single_conversation(conv_data, source_path, attachment_root)
                if conv and conv.messages:
                    yield conv
            except Exception as e:
                conv_id = conv_data.get("id", "unknown")
                print(f"Warning: Failed to parse conversation {conv_id}: {e}")
                continue

    def _parse_single_conversation(
        self, 
        data: dict[str, Any], 
        source_path: str,
        attachment_root: Path | None = None
    ) -> Conversation | None:
        """Parse a single conversation from ChatGPT export."""
        native_id = data.get("id")
        if not native_id:
            return None

        # Extract timestamps
        create_time = data.get("create_time")
        update_time = data.get("update_time")

        if create_time:
            created_at = datetime.fromtimestamp(create_time)
        else:
            created_at = datetime.now()

        if update_time:
            updated_at = datetime.fromtimestamp(update_time)
        else:
            updated_at = created_at

        # Extract messages from the mapping structure
        messages = self._extract_messages(data, attachment_root)

        if not messages:
            return None

        # Archive raw conversation data
        archived_path = self._archive_raw(data, native_id, "json")

        return Conversation(
            id=f"{self.source_name}:{native_id}",
            source=self.source_name,
            native_id=native_id,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            title=data.get("title"),
            metadata={
                "source_path": str(archived_path),
                "original_path": source_path,
                "model": data.get("default_model_slug"),
            },
        )

    def _extract_messages(
        self, 
        data: dict[str, Any],
        attachment_root: Path | None = None
    ) -> list[Message]:
        """Extract messages from ChatGPT's mapping structure."""
        messages: list[Message] = []
        mapping = data.get("mapping", {})
        current_node = data.get("current_node")

        # Traverse tree to get messages in correct order
        raw_messages = self._traverse_conversation_tree(mapping, current_node)

        for msg_data in raw_messages:
            author = msg_data.get("author", {})
            role = author.get("role")
            
            # Skip system messages unless they have relevant content
            if role == "system":
                # Check if it's a relevant system message (e.g. tool output)
                # For now, we'll skip generic system messages
                pass
            
            # Determine normalized role
            if role == "user":
                norm_role = "user"
            elif role in ("assistant", "tool"):
                norm_role = "assistant"
            else:
                norm_role = role or "unknown"

            content_obj = msg_data.get("content", {})
            content_type = content_obj.get("content_type", "text")
            
            # Parse content and metadata
            text_parts = []
            metadata = {
                "content_type": content_type,
                "has_code": False,
                "has_thinking": False,
                "has_web_search": False,
                "has_multimodal": False,
                "has_execution": False,
                "has_execution": False,
                "model": msg_data.get("metadata", {}).get("model_slug"),
                "attachments": [],
            }

            # Capture attachment info
            msg_metadata = msg_data.get("metadata", {})
            if "attachments" in msg_metadata:
                for att in msg_metadata["attachments"]:
                    att_name = att.get("name")
                    att_id = att.get("id")
                    local_path = None
                    
                    # Try to find the file if we have a root
                    if attachment_root and att_name:
                        # Search strategy:
                        # 1. Look for file with exact name in root
                        # 2. Look for file in user-* folders
                        candidates = list(attachment_root.glob(f"**/{att_name}"))
                        if candidates:
                            try:
                                with open(candidates[0], "rb") as f:
                                    content = f.read()
                                
                                archived = self._archive_raw(
                                    content,
                                    f"attachments/{att_name}",
                                    extension="",
                                    is_binary=True
                                )
                                local_path = str(archived)
                            except Exception:
                                pass

                    metadata["attachments"].append({
                        "id": att_id,
                        "name": att_name,
                        "mime_type": att.get("mime_type"),
                        "size": att.get("size"),
                        "local_path": local_path,
                    })

            if content_type == "text":
                parts = content_obj.get("parts", [])
                text_parts.extend([str(p) for p in parts if p])
            elif content_type == "code":
                metadata["has_code"] = True
                text_parts.append(f"```\n{content_obj.get('text', '')}\n```")
            elif content_type in ("thoughts", "reasoning_recap"):
                metadata["has_thinking"] = True
                text_parts.append(content_obj.get("text", ""))
            elif content_type == "execution_output":
                metadata["has_execution"] = True
                text_parts.append(f"Output: {content_obj.get('text', '')}")
            elif content_type in ("tether_quote", "tether_browsing_display"):
                metadata["has_web_search"] = True
                # These usually don't have main text content to display
            elif content_type == "multimodal_text":
                metadata["has_multimodal"] = True
                parts = content_obj.get("parts", [])
                for part in parts:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict):
                        if "image_url" in part:
                            text_parts.append(f"[IMAGE: {part['image_url']}]")
            else:
                # Fallback
                text_parts.append(str(content_obj.get("text", "")))

            content = "\n".join(text_parts).strip()
            
            # Skip empty messages unless they have metadata flags
            if not content and not any(metadata.values()):
                continue

            # Get timestamp
            create_time = msg_data.get("create_time")
            ts = datetime.fromtimestamp(create_time) if create_time else None

            messages.append(
                Message(
                    role=norm_role,
                    content=content,
                    timestamp=ts,
                    id=msg_data.get("id"),
                    metadata=metadata,
                )
            )

        return messages

    def _traverse_conversation_tree(
        self, mapping: dict[str, Any], current_node: str | None
    ) -> list[dict[str, Any]]:
        """Traverse OpenAI conversation tree to extract messages in order."""
        messages = []
        
        # If we have a current_node (leaf), trace back to root
        if current_node:
            node_id = current_node
            while node_id:
                node = mapping.get(node_id)
                if not node:
                    break
                
                message = node.get("message")
                if message:
                    # Check if hidden
                    metadata = message.get("metadata", {})
                    is_hidden = metadata.get("is_visually_hidden_from_conversation", False)
                    
                    if not is_hidden:
                        messages.append(message)
                
                node_id = node.get("parent")
            
            # Reverse to get chronological order
            return list(reversed(messages))
            
        # Fallback: Walk from root (depth-first, taking last child at each branch)
        # This approximates the "current" conversation state
        root_nodes = [
            nid for nid, node in mapping.items() 
            if not node.get("parent")
        ]
        
        if not root_nodes:
            return []
            
        # Start with the first root found
        curr_id = root_nodes[0]
        
        while curr_id:
            node = mapping.get(curr_id)
            if not node:
                break
                
            message = node.get("message")
            if message:
                metadata = message.get("metadata", {})
                is_hidden = metadata.get("is_visually_hidden_from_conversation", False)
                if not is_hidden:
                    messages.append(message)
            
            children = node.get("children", [])
            if not children:
                break
                
            # Take the last child (usually the most recent regeneration)
            curr_id = children[-1]
            
        return messages
