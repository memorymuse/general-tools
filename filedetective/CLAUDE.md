# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FileDetective (`filedet`) is a CLI tool for intelligent file discovery and analysis across multiple project directories. It provides:
- Token counting using tiktoken (OpenAI cl100k_base encoding)
- Multi-file comparison with aggregate statistics
- Priority-based search across configured directories
- Path-based wildcards and auto-search on missing files
- Structure extraction (TOC for docs, functions/classes for code)
- Dependency analysis for Python and JavaScript/TypeScript files

## Commands

```bash
# Install globally (REQUIRED - use uv, NOT pip)
uv tool install .

# After installation, use directly
filedet <file(s)> [flags]
filedet find <pattern>
filedet grep <term> <directory>
filedet hist [directory] [-n COUNT] [-ft EXT...]
filedet reinstall                 # Rebuild and reinstall from source

# Development (run without installing)
python3 -m filedetective <args>

# Run tests
pytest tests/
```

**IMPORTANT**: Always use `uv tool install`, never `pip install`. This project uses uv for dependency management.

**Reinstalling after code changes**: Run `filedet reinstall` from anywhere. This cleans the uv cache and reinstalls from source. If uv cache issues persist, manually run `uv cache clean` first.

## Usage Examples

### Analyze Files
```bash
filedet storage.py              # Core stats
filedet storage.py -o           # Stats + structure (functions/classes)
filedet storage.py -d           # Stats + dependencies
filedet storage.py -o -d        # Stats + structure + dependencies
filedet *.py                    # Compare all Python files
filedet readme.md -o            # Show table of contents
```

### Line Ranges
Analyze specific line ranges within files (useful for token counting portions of code):
```bash
filedet file.py:10-50           # Lines 10-50 only
filedet file.py:100-            # Line 100 to end
filedet file.py:-50             # Start to line 50
filedet a.py:10-50 b.py:20-30   # Multi-file with different ranges
```

Output shows the range and context:
```
File: storage.py:10-50 (~/projects/.../storage.py)
Lines: 10-50 (41 of 342 total)

tokens:    247  │  lines:     41  │  chars:   1,823  │  size:   1.8 KB
tks/ln:    6.0  (med: 5.0)  │  chars/ln:   44.5  (med: 48.0)
```

### Analyze Directories
```bash
filedet ./src                   # All files in src/ (top-level only)
filedet ./src -r                # Recursive (include subdirectories)
filedet ./src -r -ft .py        # Recursive, Python files only
filedet ./src -r -ft .py .md    # Recursive, multiple extensions
```

**Behavior:**
- Uses filesystem check (`is_dir()`) to distinguish directories from extensionless files (Unix scripts)
- Non-recursive by default (top-level files only)
- `-r` enables recursive traversal through subdirectories
- `-ft` filters by extension (same syntax as `hist` command)
- Skips common non-content directories: `.git/`, `.venv/`, `node_modules/`, `__pycache__/`, etc.
- Skips lock files, `.pyc`, and other generated files

### Smart File Discovery

**Local-first resolution** (case-insensitive):
```bash
filedet claude.md               # Finds CLAUDE.md in current directory
filedet ./storage.py            # Explicit local, case-insensitive
```

**Global search** (requires wildcards or no extension):
```bash
filedet storage                 # Auto-wraps as *storage*, searches all dirs
filedet "*claude*"              # Explicit wildcard, searches all dirs
filedet find storage.py         # Use 'find' command for global search
```

**Behavior:**
- **Files with extensions** (e.g., `claude.md`): Local-only. If not found, shows error with suggestion to use `find`
- **Names without extensions** (e.g., `storage`): Auto-wraps in `*pattern*`, searches configured directories
- **Explicit wildcards** (e.g., `*storage*`): Searches configured directories as-is
- Case-insensitive matching (`CLAUDE.md` and `claude.md` are equivalent locally)
- Single match → Analyzes immediately
- Multiple matches → Shows all (sorted by recency) and asks to refine

### Path-Based Patterns
Patterns containing `/` match against full path from search roots:
```bash
filedet "cc-*/drafts/*.md"                    # Files in cc-* directories
filedet "*/memos/design/*.md"                 # Across all streams
filedet "claude-mds/*/drafts/project*.md"     # Multi-level wildcards
filedet ~/.claude/CLAUDE.md "streams/*/CLAUDE.md"  # Combine with local files
```

### Find Command (Search Without Analyzing)
```bash
filedet find storage.py                  # Find in configured project directories
filedet find storage.py -l               # Find in current directory (local)
filedet find "*.py" -l                   # Find all Python files locally
filedet find docs/*ARCH*.md docs/*VISION*.md  # Multiple patterns at once
```

Multi-pattern benefits: Results combined, deduplicated, sorted by recency.

### Content Search (Grep)
```bash
filedet grep "EventManager" ~/projects/muse-v1
filedet grep "TODO" .
```

### History (Recent Files)
```bash
filedet hist                      # 15 most recent files in cwd
filedet hist -n 30                # Adjust count
filedet hist ~/projects -n 10     # Specific directory
filedet hist -ft .md .py          # Filter by extension (with or without dot)
filedet hist -ft .env* .*local    # Wildcard patterns for dotfiles
filedet hist -g                   # Show git status column (M/A/?/✓)
filedet hist -gd                  # Show git status + last commit info
filedet hist -full                # Simple output: datetime + full path
filedet hist -h                   # Show hist-specific help
```

**Git status values**: `M` = modified, `A` = staged, `?` = untracked, `✓` = clean, `!` = ignored, `-` = not in repo

**Note**: `-g` and `-gd` modes hide Lines/Tokens columns to give Path more display space.

**Included dotfiles**: `.gitignore`, `.env*`, `.claude*`, `.*local`, `.editorconfig`, `.prettierrc*`, `.eslintrc*`, etc.

**Excluded**: `.git/`, `.venv/`, `node_modules/`, `__pycache__/`, `*.pyc`, `*.lock`, `.DS_Store`, etc.

## Output Examples

### Single File Analysis
```
File: storage.py (~/projects/muse-v1/core/storage.py)
Modified: 25.11.04 14:32
Type: Python

tokens:  1,247  │  lines:    342  │  chars:   8,934  │  size:   8.7 KB
tks/ln:    3.6  (med: 3.0)  │  chars/ln:   26.1  (med: 32.0)
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
Analyzed 3 files:

┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ File                  ┃ Type       ┃ Tokens ┃ Lines ┃  Chars ┃    Size ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ storage.py [largest]  │ Python     │  1,247 │   342 │  8,934 │  8.7 KB │
│ config.yaml           │ Text       │     56 │    13 │    183 │  183.0 B│
│ README.md [smallest]  │ Markdown   │     42 │    15 │    181 │  181.0 B│
└───────────────────────┴────────────┴────────┴───────┴────────┴─────────┘

Totals (3 files):
  tokens:  1,345  │  lines:    370  │  chars:   9,298  │  size:    9.1 KB
```

**Note:** Type column only appears when file types are mixed. For files of the same type, the column is hidden.

### History (`filedet hist`)
```
Recent files in ~/projects/myapp (15 shown)

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Modified (PST)   ┃ Ext    ┃ Path                  ┃ Lines ┃ Tokens ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ 25.12.08 11:19   │ .py    │ core/storage.py       │   342 │  1,247 │
│ 25.12.08 10:48   │ .md    │ README.md             │   192 │  1,884 │
│ 25.12.07 09:45   │ .yaml  │ config.yaml           │    56 │    234 │
└──────────────────┴────────┴───────────────────────┴───────┴────────┘
```

## Repository Structure

### CRITICAL: Nested Directory Structure

This repo has **two directories named `filedetective`**. This is intentional and standard Python packaging:

```
filedetective/                    # ← REPOSITORY ROOT (clone lands here)
├── CLAUDE.md                     # This file
├── README.md
├── pyproject.toml                # Package config (defines 'filedet' entry point)
├── config.yaml                   # Search directories config
│
├── filedetective/                # ← PYTHON PACKAGE (edit code HERE)
│   ├── __init__.py
│   ├── __main__.py               # Entry: `python -m filedetective`
│   ├── cli.py                    # CLI parsing, command dispatch
│   ├── config.yaml               # Package-local config copy
│   ├── core/
│   │   ├── file_finder.py        # File discovery, pattern matching
│   │   ├── file_analyzer.py      # Dispatch to analyzers
│   │   ├── history.py            # hist command
│   │   ├── git_utils.py          # Git status utilities
│   │   └── tokenizer.py          # Token counting
│   ├── analyzers/
│   │   ├── base_analyzer.py      # FileStats/AggregateStats dataclasses
│   │   ├── text_analyzer.py      # Plain text
│   │   ├── markdown_analyzer.py  # TOC extraction
│   │   ├── python_analyzer.py    # AST-based (Python)
│   │   └── javascript_analyzer.py # Regex-based (JS/TS)
│   └── utils/
│       ├── file_utils.py         # FileType enum
│       └── display.py            # Rich output formatting
│
├── tests/                        # pytest tests
└── build/                        # Build artifacts (stale - delete if issues)
```

### Agent Navigation Guide

**When editing code, ALWAYS use paths starting with `filedetective/` (the inner package):**
```
✓ filedetective/cli.py              # Correct - edits the package
✓ filedetective/utils/display.py    # Correct
✗ cli.py                            # Wrong - doesn't exist at repo root
✗ utils/display.py                  # Wrong - doesn't exist at repo root
```

**Common pitfalls:**
1. **Editing wrong location**: There are NO `.py` files at the repo root. All code is inside `filedetective/`.
2. **Stale build directory**: If changes aren't taking effect after reinstall, delete `build/` and any `*.egg-info` directories, then run `uv cache clean` before reinstalling.
3. **Finding files**: Use `ls filedetective/` to see package contents, not `ls`.

**Running during development:**
```bash
# From repo root - runs source directly (no install needed)
python3 -m filedetective <args>

# After installing with uv
filedet <args>
```

## Architecture

**Key patterns:**
- `BaseAnalyzer` abstract class: Subclasses implement `_get_type_name()` and `_analyze_specific()`
- `FileAnalyzer.analyze_file()`: Dispatches to appropriate analyzer based on `FileType`
- `FileFinder`: Two matching modes - filename-only (no `/`) vs path-based (contains `/`)
- Path-based patterns auto-try multiple depth prefixes (`pattern`, `*/pattern`, `*/*/pattern`)

## Search Priority

Configured in `config.yaml`:
1. `~/projects/muse-v1/*` (highest)
2. `~/projects/*` (excluding muse-v1, muse-v0)
3. `~/cc-projects/*`
4. `~/.claude/*`
5. `~/projects/muse-v0/*` (lowest)

## Supported File Types

**Any text-based file is analyzable** with basic stats (tokens, lines, chars). Specialized analyzers provide structure (`-o`) and dependencies (`-d`) for supported types:

| Extension(s) | Type | `-o` (structure) | `-d` (deps) | Implementation |
|--------------|------|------------------|-------------|----------------|
| `.py` | Python | Functions/classes | Imports | AST-based (accurate) |
| `.js`, `.jsx`, `.ts`, `.tsx` | JavaScript/TypeScript | Functions/classes | ES6/CommonJS imports | Regex-based (~80-90% coverage) |
| `.md` | Markdown | TOC from headers | N/A | Regex |
| `.txt` | Text | N/A | N/A | Basic stats only |
| `.json`, `.yaml`, `.yml`, `.xml`, `.toml`, etc. | Config/Other | N/A | N/A | Basic stats only (falls back to text analyzer) |

**Mixed file types:** You can analyze files of different types together. Totals are calculated across all files. A Type column appears when file types are mixed.

**Graceful flag handling:** Using `-o` or `-d` on unsupported file types silently skips (no error). Structure/deps are simply omitted from output.

**Design choice (JS/TS):** Chose regex over AST for lightweight implementation with no external dependencies. Covers most real-world patterns. Can upgrade to proper AST parser (esprima, babel) if needed.

## Token Counting

Uses tiktoken with `cl100k_base` encoding. Fallback: `words * 1.3` if tiktoken unavailable (82.6% accuracy).

## Flags

### Global flags
| Flag | Long | Description |
|------|------|-------------|
| `-l` | `--local` | Search current directory instead of configured project dirs |

### Analyze mode
| Flag | Long | Description |
|------|------|-------------|
| `-o` | `--outline` | Show structure (TOC for text, functions for code) |
| `-d` | `--deps` | Show dependencies (code files only) |
| `-r` | `--recursive` | Include subdirectories when analyzing a directory |
| `-ft` | `--filetypes` | Filter by extension(s) when analyzing a directory |

### Hist mode (`filedet hist`)
| Flag | Long | Description |
|------|------|-------------|
| `-n` | `--count` | Number of files to show (default: 15) |
| `-ft` | `--filetypes` | Filter by extension(s): `.md`, `md`, `*.env*`, `*local` |
| `-g` | `--git` | Show git status column (M/A/?/✓) |
| `-gd` | `--git-detail` | Show git status + last commit info |
| `-full` | `--full` | Simple output: datetime + full path only (no table) |

## Troubleshooting

**"File not found: X.ext"**: Files with extensions are resolved locally only. If you want to search configured directories, use:
- `filedet find X.ext` to search all directories
- `filedet "*X*"` to use wildcard pattern matching

**"Found N matches"**: Multiple files match pattern. Refine with more specific path (e.g., `"cc-*/drafts/project*.md"` instead of `"project*.md"`) or use the full path from the list shown.

**Path patterns not working**:
- Path patterns need `/`: `filedet "cc-*/drafts/*.md"`
- Quote patterns to prevent shell expansion: `filedet "*.py"` not `filedet *.py`
- Patterns match relative to each configured search root
