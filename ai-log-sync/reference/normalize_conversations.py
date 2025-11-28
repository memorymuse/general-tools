#!/usr/bin/env python3
"""
Normalize extracted conversations into unified schema.
Phase 2: Transform raw structures into consistent format across all sources.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ConversationNormalizer:
    """Normalize conversations from raw format to unified schema."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.extracted_dir = base_dir / 'data' / 'extracted'
        self.normalized_dir = base_dir / 'data' / 'normalized' / 'conversations'
        self.outputs_dir = base_dir / 'outputs'

        self.stats = {
            'claude': {'total': 0, 'by_month': {}, 'errors': []},
            'openai': {'total': 0, 'by_month': {}, 'errors': []},
        }

    def normalize_claude_message(self, msg: Dict, index: int) -> Dict:
        """Normalize a single Claude message."""
        # Determine author type and subtypes
        sender = msg.get('sender', 'unknown')
        author_type = 'user' if sender == 'human' else 'assistant'
        author_source = 'human' if sender == 'human' else 'claude'

        # Analyze content to determine subtypes
        subtypes = []
        has_thinking = False
        has_tools = False
        has_voice = False
        content_types = []
        tool_info = []

        for content in msg.get('content', []):
            ctype = content.get('type')
            content_types.append(ctype)

            if ctype == 'thinking':
                subtypes.append('thinking')
                has_thinking = True
            elif ctype == 'tool_use':
                subtypes.append('tool_use')
                has_tools = True
                tool_info.append({
                    'name': content.get('name'),
                    'id': content.get('id')
                })
            elif ctype == 'tool_result':
                subtypes.append('tool_result')
                has_tools = True
            elif ctype == 'voice_note':
                subtypes.append('voice')
                has_voice = True

        # Extract main text content
        text_parts = []
        for content in msg.get('content', []):
            if content.get('type') == 'text':
                text_parts.append(content.get('text', ''))

        main_content = '\n'.join(text_parts)

        # Build normalized message
        normalized = {
            'message_id': f"claude:{msg.get('uuid', 'unknown')}",
            'index': index,
            'timestamp': msg.get('created_at'),
            'author': {
                'type': author_type,
                'source': author_source,
                'original_role': sender,
                'subtypes': subtypes
            },
            'content': main_content,
            'metadata': {
                'content_types': content_types,
                'has_thinking': has_thinking,
                'has_tools': has_tools,
                'has_voice': has_voice,
                'has_attachments': len(msg.get('attachments', [])) > 0,
                'attachment_count': len(msg.get('attachments', [])),
                'word_count': len(main_content.split()) if main_content else 0
            }
        }

        # Add tool info if present
        if tool_info:
            normalized['metadata']['tools'] = tool_info

        # Add thinking preview if present
        if has_thinking:
            for content in msg.get('content', []):
                if content.get('type') == 'thinking':
                    thinking_text = content.get('thinking', '')
                    normalized['metadata']['thinking_preview'] = thinking_text[:200]
                    break

        return normalized

    def normalize_openai_message(self, msg: Dict, index: int) -> Dict:
        """Normalize a single OpenAI message."""
        # Determine author
        author_role = msg.get('author', {}).get('role', 'unknown')
        content_obj = msg.get('content', {})
        content_type = content_obj.get('content_type', 'text')

        # Map to normalized author type
        if author_role == 'user':
            author_type = 'user'
            author_source = 'human'
        elif author_role == 'assistant':
            author_type = 'assistant'
            author_source = 'chatgpt'
        elif author_role == 'tool':
            author_type = 'tool'
            author_source = 'chatgpt'
        elif author_role == 'system':
            author_type = 'system'
            author_source = 'chatgpt'
        else:
            author_type = 'unknown'
            author_source = 'unknown'

        # Determine subtypes based on content
        subtypes = []
        has_code = content_type == 'code'
        has_thoughts = content_type in ['thoughts', 'reasoning_recap']
        has_execution = content_type == 'execution_output'
        has_web_search = content_type in ['tether_quote', 'tether_browsing_display']
        has_multimodal = content_type == 'multimodal_text'

        if has_code:
            subtypes.append('code')
        if has_thoughts:
            subtypes.append('reasoning')
        if has_execution:
            subtypes.append('execution_output')
        if has_web_search:
            subtypes.append('web_search')
        if has_multimodal:
            subtypes.append('multimodal')

        # Extract text content
        parts = content_obj.get('parts', [])
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                # Handle multimodal content
                if 'text' in part:
                    text_parts.append(part['text'])
                elif 'image_url' in part:
                    text_parts.append(f"[IMAGE: {part['image_url']}]")

        main_content = '\n'.join(text_parts)

        # Parse timestamp
        create_time = msg.get('create_time')
        if create_time:
            timestamp = datetime.fromtimestamp(create_time).isoformat() + 'Z'
        else:
            timestamp = None

        # Build normalized message
        normalized = {
            'message_id': f"openai:{msg.get('id', 'unknown')}",
            'index': index,
            'timestamp': timestamp,
            'author': {
                'type': author_type,
                'source': author_source,
                'original_role': author_role,
                'subtypes': subtypes
            },
            'content': main_content,
            'metadata': {
                'content_type': content_type,
                'has_code': has_code,
                'has_thoughts': has_thoughts,
                'has_execution': has_execution,
                'has_web_search': has_web_search,
                'has_multimodal': has_multimodal,
                'status': msg.get('status'),
                'word_count': len(main_content.split()) if main_content else 0
            }
        }

        return normalized

    def normalize_claude_conversation(self, raw_file: Path) -> Dict:
        """Normalize a Claude conversation."""
        with open(raw_file, 'r') as f:
            raw = json.load(f)

        # Parse date for folder structure
        created_at = raw.get('created_at', '')
        if created_at:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            year_month = dt.strftime('%Y-%m')
        else:
            year_month = 'unknown'

        # Normalize messages
        normalized_messages = []
        for idx, msg in enumerate(raw.get('chat_messages', [])):
            normalized_msg = self.normalize_claude_message(msg, idx)
            normalized_messages.append(normalized_msg)

        # Build normalized conversation
        conversation_id = raw.get('uuid', 'unknown')

        normalized = {
            'conversation_id': f"claude:{conversation_id}",
            'source': 'claude',
            'title': raw.get('name', 'Untitled'),
            'created_at': created_at,
            'updated_at': raw.get('updated_at'),
            'summary': raw.get('summary'),
            'message_count': len(normalized_messages),
            'metadata': {
                'original_id': conversation_id,
                'account_uuid': raw.get('account', {}).get('uuid'),
                'raw_file': str(raw_file.relative_to(self.base_dir)),
                'total_words': sum(m['metadata']['word_count'] for m in normalized_messages)
            },
            'messages': normalized_messages
        }

        return normalized, year_month

    def traverse_openai_tree(self, mapping: Dict, current_node: str = None) -> List[Dict]:
        """Traverse OpenAI conversation tree to extract messages in order."""
        messages = []
        visited = set()

        def walk_tree(node_id: str):
            if node_id not in mapping or node_id in visited:
                return

            visited.add(node_id)
            node = mapping[node_id]
            message = node.get('message')

            # Add non-empty, non-hidden messages
            if message and message.get('author'):
                metadata = message.get('metadata', {})
                is_hidden = metadata.get('is_visually_hidden_from_conversation', False)

                content = message.get('content', {})
                parts = content.get('parts', [])
                has_content = any(str(p).strip() for p in parts if p)

                if not is_hidden and has_content:
                    messages.append(message)

            # Walk children in order
            for child_id in node.get('children', []):
                walk_tree(child_id)

        # Find root nodes
        root_nodes = []
        for node_id, node in mapping.items():
            parent = node.get('parent')
            if parent is None or parent == 'client-created-root' or parent not in mapping:
                if node_id == 'client-created-root':
                    root_nodes.insert(0, node_id)
                else:
                    root_nodes.append(node_id)

        # Walk from each root
        for root in root_nodes:
            walk_tree(root)

        return messages

    def normalize_openai_conversation(self, raw_file: Path) -> Dict:
        """Normalize an OpenAI conversation."""
        with open(raw_file, 'r') as f:
            raw = json.load(f)

        # Parse date for folder structure
        create_time = raw.get('create_time')
        if create_time:
            dt = datetime.fromtimestamp(create_time)
            year_month = dt.strftime('%Y-%m')
            created_at = dt.isoformat() + 'Z'
        else:
            year_month = 'unknown'
            created_at = None

        update_time = raw.get('update_time')
        if update_time:
            updated_at = datetime.fromtimestamp(update_time).isoformat() + 'Z'
        else:
            updated_at = None

        # Extract messages from tree structure
        mapping = raw.get('mapping', {})
        raw_messages = self.traverse_openai_tree(mapping)

        # Normalize messages
        normalized_messages = []
        for idx, msg in enumerate(raw_messages):
            normalized_msg = self.normalize_openai_message(msg, idx)
            normalized_messages.append(normalized_msg)

        # Build normalized conversation
        conversation_id = raw.get('id', raw.get('conversation_id', 'unknown'))

        normalized = {
            'conversation_id': f"openai:{conversation_id}",
            'source': 'openai',
            'title': raw.get('title', 'Untitled'),
            'created_at': created_at,
            'updated_at': updated_at,
            'summary': None,  # OpenAI doesn't have auto-generated summaries
            'message_count': len(normalized_messages),
            'metadata': {
                'original_id': conversation_id,
                'model': raw.get('default_model_slug'),
                'is_archived': raw.get('is_archived'),
                'raw_file': str(raw_file.relative_to(self.base_dir)),
                'total_words': sum(m['metadata']['word_count'] for m in normalized_messages)
            },
            'messages': normalized_messages
        }

        return normalized, year_month

    def normalize_all(self):
        """Normalize all extracted conversations."""
        print("CONVERSATION NORMALIZATION - PHASE 2")
        print("Transforming to unified schema")
        print()

        index_entries = []

        # Normalize Claude conversations
        print("="*60)
        print("NORMALIZING CLAUDE CONVERSATIONS")
        print("="*60)

        claude_dir = self.extracted_dir / 'claude'
        if claude_dir.exists():
            for raw_file in claude_dir.rglob('*.json'):
                try:
                    normalized, year_month = self.normalize_claude_conversation(raw_file)

                    # Create output directory
                    output_dir = self.normalized_dir / year_month
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Write normalized file
                    output_file = output_dir / raw_file.name
                    with open(output_file, 'w') as f:
                        json.dump(normalized, f, indent=2)

                    # Track stats
                    self.stats['claude']['total'] += 1
                    self.stats['claude']['by_month'][year_month] = \
                        self.stats['claude']['by_month'].get(year_month, 0) + 1

                    # Add to index
                    index_entries.append({
                        'conversation_id': normalized['conversation_id'],
                        'source': 'claude',
                        'original_id': normalized['metadata']['original_id'],
                        'title': normalized['title'],
                        'created_at': normalized['created_at'],
                        'year_month': year_month,
                        'message_count': normalized['message_count'],
                        'word_count': normalized['metadata']['total_words'],
                        'has_summary': normalized['summary'] is not None,
                        'file': str(output_file.relative_to(self.base_dir))
                    })

                    if self.stats['claude']['total'] % 50 == 0:
                        print(f"  Normalized {self.stats['claude']['total']} conversations...")

                except Exception as e:
                    error_msg = f"Error normalizing {raw_file.name}: {e}"
                    print(f"  WARNING: {error_msg}")
                    self.stats['claude']['errors'].append(error_msg)

        print(f"✓ Normalized {self.stats['claude']['total']} Claude conversations")

        # Normalize OpenAI conversations
        print("\n" + "="*60)
        print("NORMALIZING OPENAI CONVERSATIONS")
        print("="*60)

        openai_dir = self.extracted_dir / 'openai'
        if openai_dir.exists():
            for raw_file in openai_dir.rglob('*.json'):
                try:
                    normalized, year_month = self.normalize_openai_conversation(raw_file)

                    # Create output directory
                    output_dir = self.normalized_dir / year_month
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Write normalized file
                    output_file = output_dir / raw_file.name
                    with open(output_file, 'w') as f:
                        json.dump(normalized, f, indent=2)

                    # Track stats
                    self.stats['openai']['total'] += 1
                    self.stats['openai']['by_month'][year_month] = \
                        self.stats['openai']['by_month'].get(year_month, 0) + 1

                    # Add to index
                    index_entries.append({
                        'conversation_id': normalized['conversation_id'],
                        'source': 'openai',
                        'original_id': normalized['metadata']['original_id'],
                        'title': normalized['title'],
                        'created_at': normalized['created_at'],
                        'year_month': year_month,
                        'message_count': normalized['message_count'],
                        'word_count': normalized['metadata']['total_words'],
                        'has_summary': normalized['summary'] is not None,
                        'file': str(output_file.relative_to(self.base_dir))
                    })

                    if self.stats['openai']['total'] % 50 == 0:
                        print(f"  Normalized {self.stats['openai']['total']} conversations...")

                except Exception as e:
                    error_msg = f"Error normalizing {raw_file.name}: {e}"
                    print(f"  WARNING: {error_msg}")
                    self.stats['openai']['errors'].append(error_msg)

        print(f"✓ Normalized {self.stats['openai']['total']} OpenAI conversations")

        return index_entries

    def write_index(self, index_entries: List[Dict]):
        """Write normalized index file."""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.outputs_dir / 'index-normalized.jsonl'

        # Sort by date
        index_entries.sort(key=lambda x: x['created_at'] or '')

        with open(index_file, 'w') as f:
            for entry in index_entries:
                f.write(json.dumps(entry) + '\n')

        print(f"\n✓ Wrote index: {index_file}")
        print(f"  Total entries: {len(index_entries)}")

    def write_stats(self):
        """Write normalization statistics."""
        stats_file = self.outputs_dir / 'normalization-stats.json'

        total = self.stats['claude']['total'] + self.stats['openai']['total']

        summary = {
            'normalization_timestamp': datetime.now().isoformat(),
            'total_conversations': total,
            'by_source': {
                'claude': self.stats['claude']['total'],
                'openai': self.stats['openai']['total']
            },
            'claude_by_month': self.stats['claude']['by_month'],
            'openai_by_month': self.stats['openai']['by_month'],
            'errors': {
                'claude': self.stats['claude']['errors'],
                'openai': self.stats['openai']['errors']
            }
        }

        with open(stats_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n✓ Wrote stats: {stats_file}")

    def print_summary(self):
        """Print normalization summary."""
        print("\n" + "="*60)
        print("NORMALIZATION SUMMARY")
        print("="*60)

        total = self.stats['claude']['total'] + self.stats['openai']['total']

        print(f"\nTotal conversations normalized: {total}")
        print(f"  Claude: {self.stats['claude']['total']}")
        print(f"  OpenAI: {self.stats['openai']['total']}")

        total_errors = len(self.stats['claude']['errors']) + len(self.stats['openai']['errors'])
        if total_errors > 0:
            print(f"\n⚠ Total errors: {total_errors}")
        else:
            print(f"\n✓ No errors")

    def run(self):
        """Execute full normalization process."""
        print("\n" + "="*60)
        print("Starting normalization...")
        print("="*60 + "\n")

        # Normalize all conversations
        index_entries = self.normalize_all()

        # Write index
        self.write_index(index_entries)

        # Write stats
        self.write_stats()

        # Print summary
        self.print_summary()

        print("\n" + "="*60)
        print("NORMALIZATION COMPLETE")
        print("="*60)
        print(f"\nNormalized files location: {self.normalized_dir}")
        print(f"Index location: {self.outputs_dir / 'index-normalized.jsonl'}")
        print()


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent

    print(f"Base directory: {base_dir}")

    normalizer = ConversationNormalizer(base_dir)
    normalizer.run()


if __name__ == '__main__':
    main()
