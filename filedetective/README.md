# FileDetective (`filedet`)

Intelligent file discovery and analysis CLI tool for multiple project directories.

## Features

- **Token counting** using tiktoken (OpenAI cl100k_base)
- **Multi-file comparison** with aggregate statistics
- **Priority-based search** across configured directories
- **Path-based wildcards** - Match files by directory structure (like `find -path`)
- **Auto-search on missing files** - Type partial names, get instant results
- **Structure extraction** (TOC for docs, functions/classes for code)
- **Dependency analysis** for Python and JavaScript/TypeScript files
- **Content search** (grep functionality)
- **Beautiful output** using Rich library

## Installation

### 1. Clone/Copy

The tool lives in `~/projects/general_tools/filedetective/`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies:
- `rich` - Beautiful terminal output
- `pyyaml` - Configuration parsing
- `tiktoken` - Token counting

### 3. Set Up Alias

Add to your `.bashrc` or `.zshrc`:

```bash
alias filedet='python3 ~/projects/general_tools/filedetective/filedet.py'
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Usage

### Analyze Files

**Single file:**
```bash
filedet storage.py              # Core stats
filedet storage.py -o           # Stats + structure (functions/classes)
filedet storage.py -d           # Stats + dependencies
filedet storage.py -o -d        # Stats + structure + dependencies
```

**Multiple files:**
```bash
filedet *.py                    # Compare all Python files
filedet file1.py file2.py       # Compare specific files
```

**Markdown/text files:**
```bash
filedet readme.md -o            # Show table of contents
```

### Smart File Discovery

FileDetective automatically searches for files if they don't exist locally:

**Filename-only patterns** (no `/` in pattern):
```bash
filedet storage                 # Auto-wraps as *storage*, finds and analyzes
filedet "project-claude"        # Searches all configured directories
filedet manager context         # Multiple files at once
```

**Path-based patterns** (contains `/`):
```bash
# Match by directory structure (like find -path)
filedet "cc-*/drafts/*.md"                    # Files in cc-* directories
filedet "*/memos/design/*.md"                 # Across all streams
filedet "claude-mds/*/drafts/project*.md"     # Multi-level wildcards

# Combine with local files
filedet ~/.claude/CLAUDE.md "streams/*/CLAUDE.md"
```

**Explicit directory patterns** (search outside configured directories):
```bash
# Specify an explicit directory to search - works even if not in config
filedet find "~/cc-projects/*SELF-REVIEW*"    # Searches ~/cc-projects/ directly
filedet find "/tmp/myproject/*test*"          # Any absolute path works
```

**How it works:**
- **Case-insensitive matching** - `CLAUDE.md` and `claude.md` are equivalent
- No extension or wildcard → Wraps in wildcards: `*pattern*`
- Contains `/` → Matches against full path from search roots
- Starts with `~/` or `/` with existing directory → Searches that directory directly
- Single match → Analyzes immediately
- Multiple matches → Shows all (sorted by recency) and asks you to refine
- **Shell-expanded files** → If shell expands `*pattern*` to existing files, returns them directly

**Implementation**: Path-based matching detects `/` in pattern, then matches against relative paths from each search root using `fnmatch`. Automatically tries multiple depth prefixes (`pattern`, `*/pattern`, `*/*/pattern`) to handle deeply nested files without requiring exact depth specification. This eliminates the need to count directory levels in glob patterns.

### Find Command

Explicitly search without analyzing (useful for collecting paths to share):

```bash
filedet find storage.py                  # Find all matches
filedet find "*.py"                      # Find all Python files
filedet find "session*.md"               # Pattern matching

# Multiple patterns at once (perfect for gathering related files)
filedet find docs/*ARCH*.md docs/*VISION*.md docs/*SYSTEM*.md
```

**Multi-pattern benefits:**
- All results combined and deduplicated
- Sorted by recency (most recent first)
- Easy to copy/paste paths for sharing with other agents

**Use case**: Gather related documentation or code files to share context with another agent. Instead of running separate searches and manually combining results, one command returns all matching files in a clean list ready for copy/paste.

Files are searched in priority order:
1. `~/projects/muse-v1/*` (highest priority)
2. `~/projects/*` (excluding muse-v1, muse-v0)
3. `~/cc-projects/*`
4. `~/.claude/*`
5. `~/projects/muse-v0/*` (lowest priority)

### Search Contents

Search file contents (grep):

```bash
filedet grep "EventManager" ~/projects/muse-v1
filedet grep "TODO" .
filedet grep "import" ~/projects/general_tools
```

## Output Examples

### Single File Analysis

```
File: storage.py (~/projects/muse-v1/core/storage.py)
Modified: 25.11.04 14:32
Type: Python

tokens:  1,247  │  lines:    342  │  chars:   8,934
tks/ln:    3.6  (med: 3)
```

### With Structure (`-o`)

```
Structure:
╭──────────────────────────────────────────────────────────╮
│ class SQLiteStorage:                                     │
│   ├── __init__() (Line 15)                              │
│   ├── initialize() (Line 28)                            │
│   ├── get_db() (Line 42)                                │
│   └── close() (Line 56)                                 │
│                                                          │
│ async def create_storage() -> SQLiteStorage: (Line 85)  │
│                                                          │
│ Summary: 1 classes, 4 methods, 1 standalone functions   │
╰──────────────────────────────────────────────────────────╯
```

### Multi-File Comparison

```
Analyzed 4 files:

┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ File           ┃ Tokens ┃ Lines ┃ Chars ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ storage.py  │  1,247 │   342 │ 8,934 │
│ manager.py  │    892 │   256 │ 6,012 │
│ context.py  │    654 │   187 │ 4,321 │
│ errors.py   │    234 │    89 │ 1,876 │
└────────────────┴────────┴───────┴───────┘

Totals (4 files):
  tokens:  3,027  │  lines:    874  │  chars:  21,143
```

### Find Results

```
Found 3 matches for "storage.py":

[1] ~/projects/muse-v1/core/storage.py
    Modified: 25.11.04 14:32
    Size: 8.9 KB

[2] ~/projects/muse-v0/core/storage.py
    Modified: 25.08.15 09:12
    Size: 6.2 KB

[3] ~/.claude/examples/storage.py
    Modified: 25.10.20 16:45
    Size: 1.2 KB
```

## Configuration

Edit `config.yaml` to customize:

- Search directories and priorities
- Directories to skip (`.git`, `node_modules`, etc.)
- File patterns to skip (`*.pyc`, etc.)
- Default settings

## Supported File Types

### Code Files (with `-o` for structure, `-d` for dependencies)

- **Python** (`.py`) - Full AST analysis
- **JavaScript/TypeScript** (`.js`, `.jsx`, `.ts`, `.tsx`) - Regex-based extraction
  - Functions, arrow functions, async functions
  - Classes with methods (including static, async)
  - Handles TypeScript type annotations and generics
  - ES6 imports and CommonJS requires
  - **Design choice**: Regex vs AST - Chose regex for lightweight implementation with no external dependencies. Covers 80-90% of real-world code patterns. Can upgrade to proper AST parser (esprima, babel) if needed.
- Go (`.go`) - _Future_
- Rust (`.rs`) - _Future_

### Text Files (with `-o` for TOC)

- Markdown (`.md`) - TOC extraction from headers
- Plain text (`.txt`)

### Config Files (stats only)

- JSON (`.json`)
- YAML (`.yaml`, `.yml`)

## Flags

| Flag | Long | Description | Applies To |
|------|------|-------------|------------|
| `-o` | `--outline` | Show structure (TOC/functions) | All files |
| `-d` | `--deps` | Show dependencies | Code files only |
| `-h` | `--help` | Show help | All commands |
| `-v` | `--version` | Show version | All commands |

## Token Counting

Uses **tiktoken** with `cl100k_base` encoding (OpenAI's tokenizer).

Fallback: If tiktoken unavailable, uses `words * 1.3` approximation (82.6% accuracy).

## Examples

```bash
# Quick analysis - auto-searches if not found locally
filedet storage

# Deep dive into structure
filedet storage.py -o -d

# Path-based pattern matching
filedet "cc-*/drafts/*.md"                    # Files in cc-* directories
filedet "*/memos/design/ss000*.md"            # Across all streams
filedet "claude-mds/projects/*/drafts/*.md"   # Multi-level wildcards

# Multiple files with patterns
filedet ~/.claude/CLAUDE.md "streams/*/CLAUDE.md"

# Find command (search without analyzing)
filedet find "*.py"
filedet find docs/*ARCH*.md docs/*VISION*.md  # Multiple patterns

# Compare all files in a directory
filedet ~/projects/muse-v1/core/*.py

# Search for TODOs in current project
filedet grep "TODO" .

# Analyze markdown with table of contents
filedet design-doc.md -o
```

## Troubleshooting

### "Found N matches"

When multiple files match your pattern, FileDetective shows options sorted by recency:
- Refine your pattern: `filedet "cc-*/drafts/project*.md"` instead of `filedet "project*.md"`
- Or use the full path from the list shown

### Mixed file types error

FileDetective requires all analyzed files to be the same type category (all code or all text). Analyze separately if needed.

### Path patterns not working

Remember:
- **Path patterns need `/`**: `filedet "cc-*/drafts/*.md"` ✅
- **Shell wildcards** may expand first: Use quotes to pass patterns to filedet
- **Relative paths**: Patterns are matched from each configured search root

### Shell says "no matches found"

If you see an error like:
```
(eval):1: no matches found: /Users/you/path/*pattern*
```

This is your shell (zsh/bash) trying to expand the glob **before** filedet runs. The shell finds no matches and fails. Fix: **quote the pattern**:
```bash
filedet find "~/cc-projects/*SELF-REVIEW*"   # Correct - quotes prevent shell expansion
filedet find ~/cc-projects/*SELF-REVIEW*     # Wrong - shell tries to expand first
```

Note: If shell expansion *does* find files (e.g., `*test*` matches `test.py` in current dir), filedet will detect these are existing files and return them directly.

## Development

**Project structure:**
```
filedetective/
├── filedet.py              # CLI entry point
├── config.yaml             # Configuration
├── core/                   # Core functionality
│   ├── file_finder.py      # Search logic
│   ├── file_analyzer.py    # Analysis dispatch
│   └── tokenizer.py        # Token counting
├── analyzers/              # File type analyzers
│   ├── base_analyzer.py
│   ├── text_analyzer.py
│   ├── markdown_analyzer.py
│   ├── python_analyzer.py
│   └── javascript_analyzer.py
└── utils/                  # Utilities
    ├── file_utils.py       # Type detection
    └── display.py          # Output formatting
```

## Credits

Built for intelligent file discovery across:
- **muse-v1** (current work)
- **general projects**
- **cc-projects** (Claude Code projects)
- **.claude** (configuration)
- **muse-v0** (legacy)

**Analysis implementations:**
- Token counting based on `analyze_markdown_notes.py`
- Python analysis adapted from `muse-codebase-mapper.py` (AST-based)
- JavaScript/TypeScript analysis using regex patterns (pragmatic approach)

## License

Internal tool. Use freely in your projects.
