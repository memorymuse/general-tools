#!/usr/bin/env python3
"""
Conversation parsers for Claude and OpenAI exports.
Normalizes both formats into a common structure for analysis.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Iterator, Set
from pathlib import Path
from datetime import datetime


@dataclass
class Message:
    """Normalized message structure."""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str  # Main text content
    timestamp: Optional[str]
    metadata: Dict  # Additional content types, tool calls, etc.


@dataclass
class Conversation:
    """Normalized conversation structure."""
    id: str
    title: str
    created_at: str
    updated_at: Optional[str]
    source: str  # 'claude' or 'openai'
    messages: List[Message]
    summary: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def get_text_content(self) -> str:
        """Get all text content as a single string."""
        parts = []
        for msg in self.messages:
            role_prefix = msg.role.upper()
            parts.append(f"{role_prefix}: {msg.content}")
        return "\n\n".join(parts)

    def count_messages_by_role(self) -> Dict[str, int]:
        """Count messages by role."""
        counts = {}
        for msg in self.messages:
            counts[msg.role] = counts.get(msg.role, 0) + 1
        return counts

    def search_content(self, query: str, case_sensitive: bool = False) -> List[Message]:
        """Search for query in message content."""
        if not case_sensitive:
            query = query.lower()

        matches = []
        for msg in self.messages:
            content = msg.content if case_sensitive else msg.content.lower()
            if query in content:
                matches.append(msg)
        return matches


class ClaudeParser:
    """Parser for Claude conversation exports."""

    @staticmethod
    def parse_message(msg_data: Dict) -> Message:
        """Parse a single Claude message."""
        role = msg_data.get('sender', 'unknown')

        # Extract text content from content array
        text_parts = []
        metadata = {
            'has_thinking': False,
            'has_tools': False,
            'tool_calls': [],
            'content_types': []
        }

        for content_item in msg_data.get('content', []):
            content_type = content_item.get('type')
            metadata['content_types'].append(content_type)

            if content_type == 'text':
                text_parts.append(content_item.get('text', ''))
            elif content_type == 'thinking':
                metadata['has_thinking'] = True
                # Optionally include thinking in metadata
                metadata['thinking'] = content_item.get('thinking', '')
            elif content_type == 'tool_use':
                metadata['has_tools'] = True
                metadata['tool_calls'].append({
                    'name': content_item.get('name'),
                    'input': content_item.get('input')
                })
            elif content_type == 'tool_result':
                metadata['has_tools'] = True

        content = '\n'.join(text_parts)
        timestamp = msg_data.get('created_at')

        return Message(
            role='user' if role == 'human' else role,
            content=content,
            timestamp=timestamp,
            metadata=metadata
        )

    @staticmethod
    def parse_conversation(convo_data: Dict) -> Conversation:
        """Parse a single Claude conversation."""
        messages = []
        for msg_data in convo_data.get('chat_messages', []):
            messages.append(ClaudeParser.parse_message(msg_data))

        return Conversation(
            id=convo_data.get('uuid', ''),
            title=convo_data.get('name', 'Untitled'),
            created_at=convo_data.get('created_at', ''),
            updated_at=convo_data.get('updated_at'),
            source='claude',
            messages=messages,
            summary=convo_data.get('summary'),
            metadata={
                'account_uuid': convo_data.get('account', {}).get('uuid')
            }
        )

    @staticmethod
    def parse_file(file_path: Path) -> Iterator[Conversation]:
        """Parse entire Claude export file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        for convo_data in data:
            yield ClaudeParser.parse_conversation(convo_data)


class OpenAIParser:
    """Parser for OpenAI conversation exports."""

    @staticmethod
    def traverse_conversation_tree(mapping: Dict, current_node: str = None) -> List[Dict]:
        """Traverse OpenAI's tree structure to extract messages in order."""
        messages = []

        def walk_tree(node_id: str, visited: Set[str]):
            if node_id not in mapping or node_id in visited:
                return

            visited.add(node_id)
            node = mapping[node_id]
            message = node.get('message')

            # Add non-empty, non-hidden messages
            if message and message.get('author'):
                # Skip hidden system messages but include visible ones
                metadata = message.get('metadata', {})
                is_hidden = metadata.get('is_visually_hidden_from_conversation', False)

                # Include if not hidden OR if it's a user/assistant message with content
                content = message.get('content', {})
                parts = content.get('parts', [])
                has_content = any(str(p).strip() for p in parts if p)

                if not is_hidden and has_content:
                    messages.append(message)

            # Walk children in order
            for child_id in node.get('children', []):
                walk_tree(child_id, visited)

        visited_nodes = set()

        # Find the root node(s) - typically "client-created-root" or nodes with no parent
        root_nodes = []
        for node_id, node in mapping.items():
            parent = node.get('parent')
            if parent is None or parent == 'client-created-root' or parent not in mapping:
                if node_id == 'client-created-root':
                    root_nodes.insert(0, node_id)  # Prioritize this root
                else:
                    root_nodes.append(node_id)

        # Walk from each root
        for root in root_nodes:
            walk_tree(root, visited_nodes)

        return messages

    @staticmethod
    def parse_message(msg_data: Dict) -> Message:
        """Parse a single OpenAI message."""
        role = msg_data['author'].get('role', 'unknown')
        content_obj = msg_data.get('content', {})
        content_type = content_obj.get('content_type', 'text')

        # Extract text content
        text_parts = []
        metadata = {
            'content_type': content_type,
            'has_code': False,
            'has_thoughts': False,
            'status': msg_data.get('status')
        }

        if content_type == 'text':
            parts = content_obj.get('parts', [])
            text_parts.extend([str(p) for p in parts if p])
        elif content_type == 'code':
            metadata['has_code'] = True
            text_parts.append(f"[CODE: {content_obj.get('text', '')}]")
        elif content_type == 'thoughts':
            metadata['has_thoughts'] = True
            text_parts.append(content_obj.get('text', ''))
        elif content_type == 'multimodal_text':
            parts = content_obj.get('parts', [])
            for part in parts:
                if isinstance(part, str):
                    text_parts.append(part)
                elif isinstance(part, dict):
                    # Handle multimodal content (images, etc.)
                    if 'image_url' in part:
                        text_parts.append(f"[IMAGE: {part['image_url']}]")
        else:
            # Other content types
            text_parts.append(str(content_obj.get('text', '')))

        content = '\n'.join(text_parts)
        timestamp = msg_data.get('create_time')
        if timestamp:
            timestamp = datetime.fromtimestamp(timestamp).isoformat()

        return Message(
            role=role,
            content=content,
            timestamp=timestamp,
            metadata=metadata
        )

    @staticmethod
    def parse_conversation(convo_data: Dict) -> Conversation:
        """Parse a single OpenAI conversation."""
        mapping = convo_data.get('mapping', {})
        current_node = convo_data.get('current_node')

        # Extract messages in order
        raw_messages = OpenAIParser.traverse_conversation_tree(mapping, current_node)
        messages = [OpenAIParser.parse_message(msg) for msg in raw_messages]

        # Parse timestamps
        created_at = convo_data.get('create_time')
        updated_at = convo_data.get('update_time')
        if created_at:
            created_at = datetime.fromtimestamp(created_at).isoformat()
        if updated_at:
            updated_at = datetime.fromtimestamp(updated_at).isoformat()

        return Conversation(
            id=convo_data.get('id', convo_data.get('conversation_id', '')),
            title=convo_data.get('title', 'Untitled'),
            created_at=created_at or '',
            updated_at=updated_at,
            source='openai',
            messages=messages,
            summary=None,
            metadata={
                'model': convo_data.get('default_model_slug'),
                'is_archived': convo_data.get('is_archived'),
                'conversation_id': convo_data.get('conversation_id')
            }
        )

    @staticmethod
    def parse_file(file_path: Path) -> Iterator[Conversation]:
        """Parse entire OpenAI export file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        for convo_data in data:
            yield OpenAIParser.parse_conversation(convo_data)


def parse_conversations(source: str, file_path: Path) -> Iterator[Conversation]:
    """
    Parse conversations from either Claude or OpenAI export.

    Args:
        source: 'claude' or 'openai'
        file_path: Path to conversations.json file

    Yields:
        Conversation objects
    """
    if source.lower() == 'claude':
        yield from ClaudeParser.parse_file(file_path)
    elif source.lower() == 'openai':
        yield from OpenAIParser.parse_file(file_path)
    else:
        raise ValueError(f"Unknown source: {source}. Must be 'claude' or 'openai'")


# Example usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python conversation_parser.py <source> <file_path>")
        print("  source: 'claude' or 'openai'")
        print("  file_path: path to conversations.json")
        sys.exit(1)

    source = sys.argv[1]
    file_path = Path(sys.argv[2])

    print(f"Parsing {source} conversations from: {file_path}\n")

    count = 0
    for convo in parse_conversations(source, file_path):
        count += 1
        print(f"[{count}] {convo.title}")
        print(f"    ID: {convo.id}")
        print(f"    Date: {convo.created_at}")
        print(f"    Messages: {len(convo.messages)}")
        role_counts = convo.count_messages_by_role()
        print(f"    Roles: {role_counts}")

        if count >= 5:  # Show first 5 as sample
            print(f"\n... and {len(list(parse_conversations(source, file_path))) - count} more")
            break
