# AI Log Sync

Aggregate AI conversation logs from multiple platforms into a single location with deduplication.

> **See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** for full architecture, schema details, and implementation phases.

## Supported Sources

**Local CLI Tools:**
- Claude Code (`~/.claude/projects/`)
- Codex CLI (`~/.codex/`) - coming soon
- Gemini CLI - via staging folder

**Web Exports:**
- ChatGPT (Settings > Data Controls > Export)
- Claude.ai (Settings > Privacy > Export)
- Gemini, Grok - via staging folder

## Installation

### Prerequisites

1. **Python 3.10+**
2. **rclone** (for cloud sync)

```bash
# macOS
brew install rclone

# Linux/WSL
sudo apt install rclone

# Windows
winget install rclone
```

### Install ai-log-sync

```bash
# Option 1: Run directly (no install needed)
cd ~/projects/ai-log-sync
PYTHONPATH=src python3 -m ai_log_sync.cli --help

# Option 2: Install in editable mode (requires pip >= 21.3)
pip install -e .

# Dependencies
pip install click pyyaml
```

### Create a shell alias (recommended)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias ai-log-sync='PYTHONPATH=~/projects/ai-log-sync/src python3 -m ai_log_sync.cli'
```

Then reload: `source ~/.zshrc`

## Quick Start

### 1. Initialize

```bash
ai-log-sync init
```

This creates:
- `~/ai-log-sync/config.yaml` - Configuration file
- `~/ai-log-sync/inbox/` - Drop web export ZIPs here
- `~/ai-log-sync/staging/` - Processed files for sync

### 2. Configure rclone (one-time)

```bash
rclone config
# Follow prompts to add "gdrive" remote for Google Drive
```

### 3. Sync

```bash
# Full sync
ai-log-sync sync

# Dry run (see what would happen)
ai-log-sync sync --dry-run

# Collect locally only (no cloud push)
ai-log-sync sync --no-push
```

### 4. Check status

```bash
ai-log-sync status
```

## Usage

### Weekly Workflow

1. **Export from web platforms** (if you have new conversations):
   - ChatGPT: Settings > Data Controls > Export
   - Claude.ai: Settings > Privacy > Export
   - Download the ZIP files

2. **Move exports to inbox**:
   ```bash
   mv ~/Downloads/*chatgpt*.zip ~/ai-log-sync/inbox/
   mv ~/Downloads/*claude*.zip ~/ai-log-sync/inbox/
   ```

3. **Run sync**:
   ```bash
   ai-log-sync sync
   ```

### Deduplication

Conversations are tracked by `{source}:{native_id}`. The "fresher wins" strategy:
- New conversations are added
- Updated conversations (newer `updated_at`) replace older versions
- Unchanged conversations are skipped

This means if you revisit an old conversation and add new messages, the next sync will update the cloud copy.

## Configuration

Edit `~/ai-log-sync/config.yaml`:

```yaml
base_dir: /Users/you/ai-log-sync
inbox_dir: /Users/you/ai-log-sync/inbox
staging_dir: /Users/you/ai-log-sync/staging

sources:
  claude-code:
    enabled: true
    paths:
      - ~/.claude/projects
  chatgpt-export:
    enabled: true
    paths: []  # Uses inbox directory
  claude-web-export:
    enabled: true
    paths: []  # Uses inbox directory

cloud:
  remote_name: gdrive
  remote_path: ai-chat-logs
  enabled: true
```

### Disable cloud sync

Set `cloud.enabled: false` to use locally only.

## Output Format

### Index (`staging/index.json`)

```json
{
  "version": "1.0",
  "updated_at": "2025-11-24T16:00:00Z",
  "count": 150,
  "entries": [
    {
      "id": "claude-code:abc123",
      "source": "claude-code",
      "native_id": "abc123",
      "updated_at": "2025-11-24T10:30:00Z",
      "created_at": "2025-11-20T08:00:00Z",
      "title": "Debug memory leak",
      "message_count": 42,
      "content_hash": "sha256:abcd1234...",
      "raw_path": "logs/claude-code/abc123.json"
    }
  ]
}
```

### Conversation files (`staging/logs/{source}/{id}.json`)

Full conversation with all messages, timestamps, and metadata.

## Troubleshooting

### rclone not found

```bash
# Check installation
which rclone

# Install
brew install rclone  # macOS
sudo apt install rclone  # Linux
```

### Remote not configured

```bash
rclone config
# Add a new remote named "gdrive" with Google Drive
```

### Permission errors

Check that `~/.claude/` is readable and rclone has access to Google Drive.

## Reference Implementations

The `reference/` directory contains more thorough parsers from prior work (`~/cc-projects/claude-chatgpt-convo-evals/`):

- **conversation_parser.py** - Handles Claude thinking blocks, tool use, OpenAI tree traversal
- **normalize_conversations.py** - Detailed schema normalization with subtypes

See `reference/README.md` for details on enhancing the collectors with this prior work.

## License

MIT
