# AI Chat Log Aggregator - Implementation Plan

## Overview

A lightweight, cross-platform system to aggregate AI conversation logs from multiple sources into Google Drive with ID-based deduplication and "fresher wins" update logic.

**Target Platforms:** macOS, Windows, WSL (Ubuntu)
**Cloud Destination:** Google Drive
**Output Format:** JSON/JSONL
**Run Cadence:** Weekly manual execution per device

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Per-Device Script                         │
│  ai-log-sync.py                                              │
├─────────────────────────────────────────────────────────────┤
│  1. COLLECT      │  2. NORMALIZE    │  3. SYNC              │
│  ─────────────   │  ─────────────   │  ─────────────        │
│  - Claude Code   │  → Common JSONL  │  - Pull index.json    │
│  - Codex CLI     │    schema with   │  - Merge (ID + ts)    │
│  - Gemini CLI    │    source, ID,   │  - Push via rclone    │
│  - Web exports   │    timestamp     │                       │
│  - (Antigravity) │                  │                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Google Drive   │
                    │  /ai-chat-logs/ │
                    │  ├─ index.json  │  ← Metadata index (IDs, timestamps)
                    │  └─ logs/       │  ← Conversation files by ID
                    └─────────────────┘
```

---

## Components

### 1. Source Collectors

Each collector knows where to find logs and how to extract conversation data.

| Source | Location | Extraction Method |
|--------|----------|-------------------|
| Claude Code | `~/.claude/projects/**/*.jsonl` | Direct read, parse JSONL |
| Codex CLI | `~/.codex/` (transcripts) | Direct read |
| Gemini CLI | Use `/export jsonl` command output | User drops export to staging folder |
| claude.ai | Manual ZIP from Settings > Privacy | Unzip, parse `conversations.json` |
| chatgpt.com | Manual ZIP from Data Controls | Unzip, parse `conversations.json` |
| gemini.google.com | Manual export via Drive/extension | Parse JSON from staging folder |
| aistudio.google.com | Google Drive auto-save | Parse JSON from staging folder |
| grok.com | Manual export from account settings | Parse from staging folder |
| Antigravity | TBD - investigate local storage | Optional module |

**Staging folder pattern:** `~/ai-log-sync/inbox/` where users drop web export ZIPs.

### 2. Normalized Schema

All conversations normalized to common JSONL format with **full metadata capture**:

```json
{
  "id": "claude-code:abc123",
  "source": "claude-code",
  "native_id": "abc123",
  "updated_at": "2025-11-24T10:30:00Z",
  "created_at": "2025-11-20T08:00:00Z",
  "title": "Debug memory leak",
  "message_count": 42,
  "content_hash": "sha256:...",
  "summary": "...",              // Claude auto-generated summary if available
  "metadata": {
    "model": "claude-3-opus",   // Model used
    "total_words": 5420,        // Word count across all messages
    "has_thinking": true,       // Contains thinking/reasoning blocks
    "has_tools": true,          // Contains tool use
    "has_code": true,           // Contains code blocks/execution
    "has_attachments": false,   // File attachments
    "has_multimodal": false,    // Images or other media
    "has_web_search": false     // Web search/browsing results
  },
  "messages": [
    {
      "message_id": "msg_123",
      "index": 0,
      "timestamp": "2025-11-24T10:00:00Z",
      "author": {
        "type": "user",           // user, assistant, system, tool
        "source": "human",        // human, claude, chatgpt, tool
        "original_role": "human", // Platform's original role name
        "subtypes": []            // thinking, tool_use, tool_result, voice, code, web_search
      },
      "content": "Help me debug...",
      "metadata": {
        "content_types": ["text"],
        "has_thinking": false,
        "has_tools": false,
        "word_count": 25,
        "thinking_preview": null,   // First 200 chars of thinking if present
        "tools": []                 // Tool names/IDs if tool_use
      }
    }
  ]
}
```

### Message Content Types to Capture

| Platform | Content Type | Capture Method |
|----------|--------------|----------------|
| Claude.ai | `text` | Main content |
| Claude.ai | `thinking` | Store in metadata, flag `has_thinking` |
| Claude.ai | `tool_use` | Extract tool name/ID, flag `has_tools` |
| Claude.ai | `tool_result` | Store result, link to tool_use |
| Claude.ai | `voice_note` | Flag `has_voice`, store transcript |
| ChatGPT | `text` | Main content |
| ChatGPT | `code` | Store code, flag `has_code` |
| ChatGPT | `thoughts` / `reasoning_recap` | Flag `has_thinking` |
| ChatGPT | `execution_output` | Store output, flag `has_code` |
| ChatGPT | `tether_quote` / `tether_browsing_display` | Flag `has_web_search` |
| ChatGPT | `multimodal_text` | Extract images, flag `has_multimodal` |
| Claude Code | Tool calls | Extract from JSONL, flag `has_tools` |

### 3. Deduplication Logic

**Strategy: ID-based with "fresher wins"**

```
For each local conversation:
  1. Generate canonical ID: "{source}:{native_id}"
  2. Look up in remote index.json
  3. If not found → ADD (new conversation)
  4. If found AND local.updated_at > remote.updated_at → REPLACE
  5. If found AND local.updated_at <= remote.updated_at → SKIP
```

This handles your use case: revisiting a 2-week-old conversation updates the remote version.

### 4. Cloud Sync via rclone

```bash
# One-time setup
rclone config  # Create "gdrive" remote

# Sync command (run by script)
rclone sync ~/ai-log-sync/staging/ gdrive:ai-chat-logs/ --checksum
```

---

## Directory Structure

### Local (per device)
```
~/ai-log-sync/
├── inbox/              # Drop web export ZIPs here
│   ├── chatgpt-export.zip
│   └── claude-export.zip
├── staging/            # Processed, ready to sync
│   ├── index.json      # Local merged index
│   └── logs/           # Normalized conversation files
│       ├── claude-code/
│       ├── claude-web/
│       ├── chatgpt/
│       └── ...
├── config.yaml         # Source paths, preferences
└── sync.log            # Execution log
```

### Remote (Google Drive)
```
/ai-chat-logs/
├── index.json          # Master index of all conversations
└── logs/
    ├── claude-code/
    │   └── {id}.json
    ├── claude-web/
    ├── chatgpt/
    ├── gemini/
    └── ...
```

---

## Implementation Steps

### Phase 1: Core Infrastructure ✅ COMPLETE
1. **Create Python package structure** with CLI entry point
2. **Implement config loader** (YAML with platform-specific paths)
3. **Build normalized schema** dataclass and validation
4. **Implement index manager** (read/write index.json, merge logic)

### Phase 2: Local Source Collectors ✅ BASIC COMPLETE
5. **Claude Code collector** - parse `~/.claude/projects/**/*.jsonl`
6. **Codex CLI collector** - parse `~/.codex/` transcripts
7. **Web export processor** - unzip and parse ChatGPT/Claude ZIPs
8. **Staging folder scanner** - generic JSON/JSONL ingestion

### Phase 3: Cloud Sync ✅ COMPLETE
9. **rclone wrapper** - pull index, push changes, verify sync
10. **CLI commands**: `ai-log-sync collect`, `ai-log-sync push`, `ai-log-sync status`

### Phase 4: Enhanced Metadata Capture ⬅️ NEXT
Refactor collectors using reference implementations from `reference/`:

11. **Enhance models.py** - Add full metadata schema:
    - `Message.metadata`: content_types, has_thinking, has_tools, word_count, thinking_preview, tools list
    - `Message.author`: type, source, original_role, subtypes
    - `Conversation.metadata`: model, total_words, has_* flags, summary

12. **Enhance Claude.ai collector** (`collectors/claude_web_export.py`):
    - Use `ClaudeParser` logic from `reference/conversation_parser.py`
    - Capture: thinking blocks, tool_use/tool_result, voice_note, attachments
    - Extract summary field from export

13. **Enhance ChatGPT collector** (`collectors/chatgpt_export.py`):
    - Use `OpenAIParser.traverse_conversation_tree()` from reference
    - Filter hidden messages (`is_visually_hidden_from_conversation`)
    - Capture: code, thoughts, execution_output, tether_quote, multimodal_text
    - Extract model slug

14. **Enhance Claude Code collector** (`collectors/claude_code.py`):
    - Capture tool calls from JSONL (tool_use content blocks)
    - Extract model info from message metadata
    - Track token usage if available

### Phase 5: Polish
15. **Add Gemini CLI support** (staging folder for `/export` output)
16. **Add Antigravity support** (if storage location identified)
17. **Add dry-run mode** for testing ✅ COMPLETE
18. **Create setup script** for rclone config

---

## Dependencies

- **Python 3.10+** (available on all target platforms)
- **rclone** (free, cross-platform, simple to install)
- **PyYAML** (config parsing)
- **click** (CLI framework)

No paid services. No API keys required for local operations.

---

## Usage Flow

### Initial Setup (once per device)
```bash
# 1. Install rclone and configure Google Drive
brew install rclone  # or apt, or download
rclone config        # Interactive setup for Google Drive

# 2. Install the sync tool
pip install ai-log-sync  # or run from source

# 3. Initialize config
ai-log-sync init     # Creates ~/ai-log-sync/ and config.yaml
```

### Weekly Sync
```bash
# 1. (Optional) Drop any web export ZIPs into inbox
mv ~/Downloads/chatgpt-*.zip ~/ai-log-sync/inbox/

# 2. Run sync
ai-log-sync sync

# Output:
# Collecting from claude-code... 47 conversations
# Collecting from codex... 12 conversations
# Processing inbox... 2 files
# Merging with remote index...
#   - 15 new conversations
#   - 8 updated conversations
#   - 36 unchanged (skipped)
# Pushing to Google Drive... done
```

---

## Deduplication Details

### ID Generation by Source

| Source | Native ID Field | Canonical ID Example |
|--------|-----------------|---------------------|
| Claude Code | `sessionId` from JSONL | `claude-code:a1b2c3d4` |
| Codex CLI | Session/run ID | `codex:run_xyz789` |
| claude.ai | `uuid` from export | `claude-web:abc-def-123` |
| chatgpt.com | `id` from conversations.json | `chatgpt:conv_abc123` |
| Gemini | Varies (timestamp fallback) | `gemini:2025-11-24T10:30` |
| Grok | TBD from export format | `grok:{id}` |

### Timestamp Extraction

For "fresher wins" comparison, extract `updated_at`:
- Claude Code: Max timestamp from messages in JSONL
- ChatGPT export: `update_time` field in conversation object
- Claude.ai export: Latest message timestamp

---

## Optional Enhancements (Future)

- **Scheduled execution** via cron/Task Scheduler
- **Content search** across aggregated logs
- **Markdown index generation** for human browsing
- **Delta sync** (only upload changed files, not full resync)

---

## Key Design Decisions

1. **Python over Bash** - Cross-platform compatibility (macOS, Windows, WSL)
2. **rclone over direct API** - Simpler setup, no OAuth dance in code
3. **Flat file storage over database** - Easy to inspect, portable, no dependencies
4. **ID + timestamp dedup** - Handles conversation updates correctly
5. **Staging folder approach** - Clean separation of concerns, easy debugging
6. **Manual weekly run** - Avoids complexity of background services

---

## Prior Work Reference

**REQUIRED**: Use existing parsers from `~/cc-projects/claude-chatgpt-convo-evals/scripts/` for full metadata capture.

| File | Purpose | Key Features |
|------|---------|--------------|
| `conversation_parser.py` | Claude & OpenAI parsing | Thinking blocks, tool use, voice notes, tree traversal |
| `normalize_conversations.py` | Schema normalization | Author subtypes, word counts, monthly organization |
| `extract_conversations.py` | ZIP extraction | Raw decomposition from monolithic exports |

**Copied to**: `~/projects/ai-log-sync/reference/`

### Metadata to Capture (from reference implementations)

**Claude.ai exports:**
- `thinking` content blocks → `has_thinking`, `thinking_preview`
- `tool_use` / `tool_result` → `has_tools`, `tools[]` with name/ID
- `voice_note` → `has_voice`
- `attachments` array → `has_attachments`, `attachment_count`
- `summary` field → conversation summary

**ChatGPT exports:**
- Tree traversal via `mapping` → proper message ordering
- `is_visually_hidden_from_conversation` → filter hidden system messages
- `content_type: code` → `has_code`
- `content_type: thoughts` / `reasoning_recap` → `has_thinking`
- `content_type: execution_output` → code execution results
- `content_type: tether_quote` / `tether_browsing_display` → `has_web_search`
- `content_type: multimodal_text` → `has_multimodal`, image URLs
- `default_model_slug` → model info

**Claude Code JSONL:**
- `message.content[].type: tool_use` → `has_tools`, tool names
- `message.model` → model info
- `message.usage` → token counts (input/output/cache)

---

## Sources

- [rclone](https://rclone.org/) - Cloud sync CLI
- [claude-code-exporter](https://github.com/developerisnow/claude-code-exporter) - Reference for Claude Code log parsing
- [ChatGPT export format](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data)
- [Claude.ai export](https://support.claude.com/en/articles/9450526-how-can-i-export-my-claude-data)
- **Local prior work**: `~/cc-projects/claude-chatgpt-convo-evals/` - Thorough Claude/OpenAI parsers
