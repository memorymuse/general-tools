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
# Run the CLI (from this directory)
python3 filedet.py <file(s)> [flags]
python3 filedet.py find <pattern>
python3 filedet.py grep <term> <directory>
python3 filedet.py hist [directory] [-n COUNT] [-ft EXT...]

# Install dependencies
pip install -r requirements.txt

# Run tests (test directory exists but tests not yet implemented)
pytest tests/

# Shell alias (add to .bashrc/.zshrc for global access)
alias filedet='python3 ~/projects/general_tools/filedetective/filedet.py'
```

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

### Smart File Discovery
Files are auto-searched if not found locally:
```bash
filedet storage                 # Auto-wraps as *storage*, finds and analyzes
filedet "project-claude"        # Searches all configured directories
```

**Behavior:**
- Case-insensitive matching (`CLAUDE.md` and `claude.md` are equivalent)
- No extension/wildcard → Wraps in wildcards: `*pattern*`
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
filedet hist -h                   # Show hist-specific help
```

**Included dotfiles**: `.gitignore`, `.env*`, `.claude*`, `.*local`, `.editorconfig`, `.prettierrc*`, `.eslintrc*`, etc.

**Excluded**: `.git/`, `.venv/`, `node_modules/`, `__pycache__/`, `*.pyc`, `*.lock`, `.DS_Store`, etc.

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
│ storage.py     │  1,247 │   342 │ 8,934 │
│ manager.py     │    892 │   256 │ 6,012 │
└────────────────┴────────┴───────┴───────┘

Totals (4 files):
  tokens:  3,027  │  lines:    874  │  chars:  21,143
```

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

## Architecture

```
filedetective/
├── filedet.py              # CLI entry point, argument parsing
├── config.yaml             # Search directories, skip patterns, defaults
├── core/
│   ├── file_finder.py      # Priority-based file discovery with path/filename pattern matching
│   ├── file_analyzer.py    # Dispatch to type-specific analyzers
│   ├── history.py          # HistoryFinder for recent files (hist command)
│   └── tokenizer.py        # tiktoken wrapper with fallback
├── analyzers/
│   ├── base_analyzer.py    # Abstract base with FileStats/AggregateStats dataclasses
│   ├── text_analyzer.py    # Plain text analysis
│   ├── markdown_analyzer.py # TOC extraction from headers
│   ├── python_analyzer.py  # AST-based function/class extraction
│   └── javascript_analyzer.py # Regex-based extraction for JS/TS
└── utils/
    ├── file_utils.py       # FileType enum, type detection
    └── display.py          # Rich-based output formatting
```

**Key patterns:**
- `BaseAnalyzer` abstract class: Subclasses implement `_get_type_name()` and `_analyze_specific()`
- `FileAnalyzer.analyze_file()`: Dispatches to appropriate analyzer based on `FileType`
- `FileFinder`: Two matching modes - filename-only (no `/`) vs path-based (contains `/`)
- Path-based patterns auto-try multiple depth prefixes (`pattern`, `*/pattern`, `*/*/pattern`)

## Search Priority

Configured in `config.yaml`:
1. `~/projects/muse-v1/*` (highest)
2. `~/projects/*` (excluding muse-v1, muse-v0)
3. `~/.claude/*`
4. `~/projects/muse-v0/*` (lowest)

## Supported File Types

| Extension(s) | Type | `-o` (structure) | `-d` (deps) | Implementation |
|--------------|------|------------------|-------------|----------------|
| `.py` | Python | Functions/classes | Imports | AST-based (accurate) |
| `.js`, `.jsx`, `.ts`, `.tsx` | JavaScript/TypeScript | Functions/classes | ES6/CommonJS imports | Regex-based (lightweight, ~80-90% coverage) |
| `.md` | Markdown | TOC from headers | N/A | Regex |
| `.txt` | Text | N/A | N/A | Basic stats only |
| `.json`, `.yaml`, `.yml` | Config | N/A | N/A | Basic stats only |

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

### Hist mode (`filedet hist`)
| Flag | Long | Description |
|------|------|-------------|
| `-n` | `--count` | Number of files to show (default: 15) |
| `-ft` | `--filetypes` | Filter by extension(s): `.md`, `md`, `*.env*`, `*local` |

## Troubleshooting

**"Found N matches"**: Multiple files match pattern. Refine with more specific path (e.g., `"cc-*/drafts/project*.md"` instead of `"project*.md"`) or use the full path from the list shown.

**Mixed file types error**: All analyzed files must be same type category (all code or all text). Analyze separately if needed.

**Path patterns not working**:
- Path patterns need `/`: `filedet "cc-*/drafts/*.md"`
- Quote patterns to prevent shell expansion: `filedet "*.py"` not `filedet *.py`
- Patterns match relative to each configured search root
