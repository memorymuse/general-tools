# FileDetective v0.2 Spec: History Command

## Overview

Add `filedet hist` command to show recently modified files in a directory tree. Foundation for future git-aware file tracking.

## Command Interface

```bash
filedet hist [directory] [flags]
```

**Default behavior**: `filedet hist` → 15 most recent files in cwd, sorted by mtime descending.

### Arguments

| Arg | Long | Default | Description |
|-----|------|---------|-------------|
| `[directory]` | positional | `.` (cwd) | Target directory (recursive) |
| `-n` | `--count` | `15` | Number of results |
| `-ft` | `--filetypes` | all | Filter by extension(s). Accepts: `.md`, `md`, `*.env*`, `*local` |

### Examples

```bash
filedet hist                      # 15 recent in cwd
filedet hist -n 30                # 30 recent
filedet hist ~/projects -n 10     # 10 recent in specific dir
filedet hist -ft .md .py          # Only markdown and python
filedet hist -ft .env* .*local    # Dotfiles matching patterns
filedet hist -ft md py yaml       # Without dots works too
```

## Output Format

Table columns (Rich):
```
Modified (PST)      | Ext   | Path (relative)              | Lines | Tokens
────────────────────┼───────┼──────────────────────────────┼───────┼────────
25.12.08 14:32      | .py   | core/file_finder.py          |   297 |  1,247
25.12.08 13:15      | .md   | README.md                    |   339 |  2,145
25.12.07 09:45      | .yaml | config.yaml                  |    56 |    234
```

- DateTime format: `YY.MM.DD HH:MM` (24h, PST) - matches existing filedet format
- Path: relative to target directory, not absolute
- Sorted: most recent first (descending mtime)

## File Filtering

### Include (dotfiles with utility)

Patterns to explicitly include even though they start with `.`:
```python
UTILITY_DOTFILES = {
    ".gitignore",
    ".gitattributes",
    ".env",           # and .env*
    ".claude*",       # .claude/, .claude.md, etc.
    ".*local",        # .npmrc.local, .env.local, etc.
    ".editorconfig",
    ".prettierrc*",
    ".eslintrc*",
    ".nvmrc",
    ".python-version",
    ".tool-versions",
}
```

### Exclude (byproducts)

Reuse existing `skip_directories` from config.yaml plus:
```python
SKIP_PATTERNS_HIST = {
    # Directories (already in config.yaml)
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",

    # Files to skip
    "*.pyc", "*.pyo", "*.pyd",
    ".DS_Store",
    "*.swp", "*.swo", "*~",
    "*.db-wal", "*.db-shm",    # SQLite temp files
    "*.lock",                   # Lock files (package-lock, yarn.lock, etc.)
    ".coverage",
    "*.egg-info",
}
```

### Filetype Filter Logic (`-ft`)

```python
def normalize_extension(ext: str) -> str:
    """Normalize extension input to glob pattern.

    '.md' -> '*.md'
    'md'  -> '*.md'
    '.env*' -> '.env*' (already a pattern)
    '*local' -> '*local'
    """
    if '*' in ext:
        return ext  # Already a pattern
    if not ext.startswith('.'):
        ext = '.' + ext
    return f'*{ext}'
```

Match against filename using fnmatch, case-insensitive.

## Implementation Plan

### 1. New Module: `core/history.py`

```python
@dataclass
class HistoryEntry:
    path: str           # Absolute path
    relative_path: str  # Relative to search root
    modified_date: float
    extension: str
    lines: int
    tokens: int

class HistoryFinder:
    def __init__(self, config: dict):
        self.skip_dirs = set(config["skip_directories"])
        self.skip_patterns = config["skip_patterns"] + SKIP_PATTERNS_HIST

    def find_recent(
        self,
        directory: Path,
        count: int = 15,
        filetypes: list[str] | None = None
    ) -> list[HistoryEntry]:
        """Find most recently modified files."""
        ...
```

Key methods:
- `find_recent()` - Walk directory, collect files, sort by mtime, return top N
- `_should_include()` - Check against skip patterns and utility dotfile allowlist
- `_matches_filetypes()` - Check if file matches -ft filter

### 2. Update `filedet.py`

Add command handling:
```python
elif first_arg == "hist":
    directory = "."
    count = 15
    filetypes = None
    # Parse remaining args for -n, -ft, and positional directory
    return handle_hist(directory, count, filetypes)
```

### 3. Update `utils/display.py`

Add:
```python
def display_history_table(entries: list[HistoryEntry], base_dir: Path) -> None:
    """Display history results as Rich table."""
    table = Table(...)
    table.add_column("Modified (PST)", ...)
    table.add_column("Ext", ...)
    table.add_column("Path", ...)
    table.add_column("Lines", justify="right")
    table.add_column("Tokens", justify="right")
    ...
```

### 4. Config Updates (optional)

Could add to `config.yaml`:
```yaml
history:
  default_count: 15
  utility_dotfiles: [...]
  additional_skip_patterns: [...]
```

Or keep hardcoded initially for simplicity.

## Help Text Updates

### `filedet -h` (main help)

Add to epilog examples:
```
  # History (recent files)
  filedet hist                    # 15 most recent files in cwd
  filedet hist -n 30              # Adjust count
  filedet hist -ft .md .py        # Filter by file type
```

### `filedet hist -h` (subcommand help)

```
usage: filedet hist [directory] [-n COUNT] [-ft EXT [EXT ...]]

Show recently modified files in a directory tree.

positional arguments:
  directory             Directory to search (default: current directory)

optional arguments:
  -h, --help            Show this help message and exit
  -n, --count COUNT     Number of files to show (default: 15)
  -ft, --filetypes EXT [EXT ...]
                        Filter by file extension(s). Accepts: .md, md, *.env*, *local

Examples:
  filedet hist                      # 15 recent in current directory
  filedet hist ~/projects -n 10     # 10 recent in specific directory
  filedet hist -ft .md .py          # Only markdown and python files
  filedet hist -ft .env* .*local    # Dotfiles matching patterns
```

Implementation: Use subparsers in argparse for proper `hist -h` support.

## File Changes Summary

| File | Change |
|------|--------|
| `core/history.py` | NEW - HistoryFinder class |
| `filedet.py` | Add `hist` subcommand with subparser, update main help epilog |
| `utils/display.py` | Add `display_history_table()` |
| `config.yaml` | Optional: add history section |
| `CLAUDE.md` | Document new command |

## Edge Cases

1. **Empty directory**: Print "No files found" message
2. **No matches for -ft**: Print "No files matching [extensions] found"
3. **Permission errors**: Skip silently (like existing FileFinder)
4. **Binary files**: Include in listing but token count may be inaccurate (acceptable)
5. **Symlinks**: Don't follow (consistent with existing behavior)
6. **Very long paths**: Truncate with `...` if exceeds reasonable column width

## Future Extensions (v0.3+)

Reserved flags for git integration:
- `-g, --git`: Add git columns (last_commit, tracked/untracked)
- `--since <date>`: Filter by date range
- `--author <name>`: Filter by git author
- `--changes`: Show files with uncommitted changes

These are NOT in scope for v0.2.

## Testing

Minimal test cases:
1. `hist` in empty directory → "No files found"
2. `hist` with `-n 5` → returns exactly 5
3. `hist` with `-ft .md` → only .md files
4. `hist` with `-ft md .py` → both types, mixed format input
5. Verify utility dotfiles included (.gitignore, .env)
6. Verify byproducts excluded (.pyc, .DS_Store)
7. Verify relative paths are correct
8. Verify PST timezone conversion

## Definition of Done

- [x] `filedet hist` works with defaults
- [x] `-n` flag works
- [x] `-ft` flag works (single and multiple, with/without dots, with wildcards)
- [x] Utility dotfiles included
- [x] Byproducts excluded
- [x] Output is clean Rich table
- [x] Relative paths displayed correctly
- [x] CLAUDE.md updated
- [ ] Basic test coverage (deferred - manual testing done)
