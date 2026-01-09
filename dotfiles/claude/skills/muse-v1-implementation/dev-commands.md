# Development Commands - Quick Reference

Common commands for Muse v1 development.

## Environment Setup

### Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

```bash
# Required in .env file
MUSE_DB_PATH=/path/to/muse.db
MUSE_USER_ID=default
MUSE_USER_EMAIL=default@local
MUSE_STREAM_NAME=stream-name
MUSE_AGENT_NAME=claude-mcp
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Tests

```bash
# Single file
pytest tests/domain/events/test_task_service.py

# Single test
pytest tests/domain/events/test_task_service.py::test_create_task

# By pattern
pytest -k "test_task"
```

### With Coverage

```bash
# All modules
pytest --cov=core --cov=domain --cov=platform_layer

# With HTML report
pytest --cov=core --cov=domain --cov-report=html
```

### Test Options

```bash
# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run last failed
pytest --lf

# Parallel execution
pytest -n auto
```

## CLI Commands

### Capture Events

```bash
# Capture thought
muse capture thought "An idea about caching"

# Capture task with priority
muse capture task "Implement OAuth" --priority high

# Capture decision with reason
muse capture decision "Use SQLite" --reason "Simplicity for v1"

# Capture memo
muse capture memo "Session summary..."
```

### Query Events

```bash
# Recent thoughts
muse query thoughts --recent

# Tasks by status
muse query tasks --status pending
muse query tasks --status completed

# All events with limit
muse query all --limit 20
```

### Stream Management

```bash
# Create new stream
muse stream create "feature-name" --enable-git

# List streams
muse stream list

# Switch stream
muse stream switch "feature-name"

# Archive stream
muse stream archive "old-feature"
```

### Status

```bash
# Current status
muse status

# With verbose output
muse status --verbose
```

## MCP Servers

### Start Servers

```bash
# Capture server (events)
python platform_layer/mcp/capture_server.py

# Query server (read operations)
python platform_layer/mcp/query_server.py

# Memory server (comprehensive)
python platform_layer/mcp/memory_server.py
```

### Server Ports (default)

| Server | Purpose |
|--------|---------|
| capture_server | Event capture operations |
| query_server | Read/query operations |
| memory_server | Memory management, MRCs |

## Database Operations

### Location

```bash
# Default location (from MUSE_DB_PATH)
echo $MUSE_DB_PATH

# Or in config
cat .env | grep MUSE_DB_PATH
```

### Direct SQLite Access

```bash
# Open database
sqlite3 $MUSE_DB_PATH

# Common queries
.tables
SELECT * FROM events LIMIT 5;
SELECT * FROM memories WHERE is_active = 1;
.quit
```

### Backup

```bash
# Simple file copy
cp $MUSE_DB_PATH muse_backup_$(date +%Y%m%d).db
```

## Code Quality

### Type Checking

```bash
# Run mypy
mypy core domain platform_layer

# Strict mode
mypy --strict core
```

### Linting

```bash
# Ruff (if configured)
ruff check .

# With auto-fix
ruff check --fix .
```

### Formatting

```bash
# Black
black core domain platform_layer tests

# Check only (don't modify)
black --check .
```

## Git Workflow

### Feature Branch

```bash
# Create and switch
git checkout -b feature/my-feature

# Push with upstream
git push -u origin feature/my-feature
```

### Commit Pattern

```bash
# After tests
git add tests/test_feature.py
git commit -m "test: Add tests for feature X"

# After implementation
git add feature.py
git commit -m "feat: Implement feature X"
```

### Pre-Push Checks

```bash
# Run tests
pytest

# Check status
git status

# Verify branch
git branch -v
```

## Debugging

### Python Debugger

```python
# Add breakpoint in code
breakpoint()

# Or
import pdb; pdb.set_trace()
```

### Logging

```bash
# Run with debug logging
LOGLEVEL=DEBUG pytest tests/

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Event Inspection

```bash
# View recent events in DB
sqlite3 $MUSE_DB_PATH "SELECT id, type, content FROM events ORDER BY timestamp DESC LIMIT 10;"
```

## Quick Reference Card

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=core --cov=domain` |
| Capture thought | `muse capture thought "..."` |
| Query tasks | `muse query tasks` |
| Create stream | `muse stream create "name"` |
| Check status | `muse status` |
| Start MCP | `python platform_layer/mcp/memory_server.py` |
