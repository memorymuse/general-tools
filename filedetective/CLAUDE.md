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
Analyzed 3 files:

┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ File                  ┃ Type       ┃ Tokens ┃ Lines ┃ Chars ┃ Words ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ storage.py [largest]  │ Python     │  1,247 │   342 │ 8,934 │     - │
│ config.yaml           │ Text       │     56 │    13 │   183 │    23 │
│ README.md [smallest]  │ Markdown   │     42 │    15 │   181 │    30 │
└───────────────────────┴────────────┴────────┴───────┴───────┴───────┘

Totals (3 files):
  tokens:  1,345  │  lines:    370  │  chars:  9,298  │  words:  53
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

```
filedetective/                    # Repository root
├── CLAUDE.md                     # This file
├── README.md
├── pyproject.toml                # Package configuration
├── requirements.txt
├── config.yaml                   # Search directories, skip patterns, defaults
├── filedetective/                # Main package (installed as 'filedetective')
│   ├── __init__.py
│   ├── __main__.py               # Entry point for `python -m filedetective`
│   ├── cli.py                    # CLI argument parsing, command dispatch
│   ├── config.yaml               # Package-local config copy
│   ├── core/
│   │   ├── file_finder.py        # Priority-based file discovery, pattern matching
│   │   ├── file_analyzer.py      # Dispatch to type-specific analyzers
│   │   ├── history.py            # HistoryFinder for recent files (hist command)
│   │   ├── git_utils.py          # Git status and commit info utilities
│   │   └── tokenizer.py          # tiktoken wrapper with fallback
│   ├── analyzers/
│   │   ├── base_analyzer.py      # Abstract base with FileStats/AggregateStats dataclasses
│   │   ├── text_analyzer.py      # Plain text analysis
│   │   ├── markdown_analyzer.py  # TOC extraction from headers
│   │   ├── python_analyzer.py    # AST-based function/class extraction
│   │   └── javascript_analyzer.py # Regex-based extraction for JS/TS
│   └── utils/
│       ├── file_utils.py         # FileType enum, type detection
│       └── display.py            # Rich-based output formatting
├── tests/                        # Test directory (pytest)
│   ├── fixtures/                 # Sample files for testing
│   └── test_file_analyzer.py
└── build/                        # Build artifacts (gitignored)
```

**Running the tool:**
```bash
# From repo root (development)
python3 -m filedetective <args>

# If installed via pip
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
