# FileDetective: Design & Implementation Plan

**Version**: 1.1 (Action-Oriented Design)
**Created**: 2025-11-07
**Updated**: 2025-11-07 (Simplified to action-based commands)
**Status**: Draft - Awaiting review of existing scripts for implementation details

---

## Executive Summary

FileDetective (`filedet`) is a CLI tool for intelligent file discovery and analysis across multiple project directories. It provides token counts, structural analysis (TOC for docs, functions for code), and multi-file comparison with smart search prioritization.

**Core Value**: Unified file intelligence across Claude, Muse v1/v0, and general projects with priority-based search and automatic type detection.

**Design Philosophy**: Action-oriented commands (analyze, find, grep) rather than type-based modes (code vs docs). Auto-detection handles file type differences transparently.

**Primary Use Cases**:
1. Quick stats on any file without remembering full paths
2. Compare multiple files (e.g., all Python modules in a package)
3. Discovery via partial filename or content search
4. Structural analysis (TOC for docs, function lists for code)

---

## Installation & Access

**Location**: `~/projects/general_tools/filedetective/`
**Command**: `filedet` (shortened from filedetective for faster typing)
**Config**: `~/projects/general_tools/filedetective/config.yaml`
**Setup**: Add to `.bashrc` or `.zshrc`:
```bash
alias filedet='python3 ~/projects/general_tools/filedetective/filedet.py'
```

---

## Search Directories & Priority

FileDetective searches these directories in priority order:

1. **Priority 1**: `~/projects/muse-v1/*` (including subdirectories)
2. **Priority 2**: `~/projects/*` (EXCLUDING muse-v1/ and muse-v0/)
3. **Priority 3**: `~/.claude/*`
4. **Priority 4**: `~/projects/muse-v0/*`

**Priority Rules**:
- When multiple files match, prioritize by directory rank
- Secondary sort: Last modified date (newest first)
- Search is recursive within each directory
- Automatic exclusions: `.git/`, `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `.pyc` files

**Rationale**: Current work (muse-v1) gets highest priority, legacy (muse-v0) lowest. User configuration (.claude) in middle. General projects catch everything else.

---

## Command Structure (Action-Oriented)

### Default Mode: Analyze
```bash
filedet <file(s)>              # Core stats (tokens, lines, chars, words)
filedet <file> -o              # Stats + structure (functions/TOC)
filedet <file> -d              # Stats + dependencies (code only)
filedet <file> -o -d           # Stats + structure + dependencies
```

**Auto-detection**: File type (code vs text) detected automatically. No need to specify.

**Multi-file**: Passing multiple files automatically enters comparison mode (individual + aggregate stats).

### Discovery Mode: Find
```bash
filedet find <pattern>         # Find files by filename/pattern
```

Searches priority directories, returns all matches with metadata (path, date, size).

### Content Search Mode: Grep
```bash
filedet grep <term> <dir>      # Search file contents
filedet grep <term> .          # Search current directory
```

Returns matching files with line numbers and context snippets.

## Core Usage Patterns

### Pattern 1: Quick File Analysis
```bash
filedet storage.py             # Auto-finds, shows core stats
filedet ~/projects/muse-v1/core/storage.py  # Exact path works too
```

**Behavior**:
- If filename unique → analyze directly
- If multiple matches → error with list of options
- Use `filedet find` to see all matches

### Pattern 2: Structural Analysis
```bash
filedet readme.md -o           # Show TOC for markdown
filedet storage.py -o          # Show functions for Python
filedet storage.py -o -d       # Show functions + imports
```

**Auto-detection**:
- Markdown/text → TOC from headers
- Python → Functions/classes via AST
- TypeScript/JS → Functions/classes (future)

### Pattern 3: Multi-File Comparison
```bash
filedet *.py                   # Compare all Python files
filedet file1.py file2.py      # Compare specific files
filedet ~/projects/muse-v1/core/*.py  # Compare module files
```

**Output**: Individual stats for each + aggregate totals, ranked by token count.

### Pattern 4: File Discovery
```bash
filedet find storage.py        # List all matches
filedet find "session*.md"     # Pattern matching
filedet find "*.py"            # All Python files
```

**Returns**: All matching files across priority directories with metadata.

### Pattern 5: Content Search
```bash
filedet grep "EventManager" ~/projects/muse-v1
filedet grep "TODO" .
filedet grep "session handoff" ~/.claude
```

**Returns**: Files containing term(s) with line numbers and context.

---

## Output Specifications

### Default Output (Core Stats Only)

**Code Files** (Python, TypeScript, etc.):
```
File: storage.py (~/projects/muse-v1/core/storage.py)
Modified: 25.11.04 14:32
Type: Python

tokens:  1,247  |  lines:    342  |  chars:   8,934
tks/ln:    3.6  (med: 3)
```

**Text/Markdown Files** (includes word metrics):
```
File: readme.md (~/projects/muse-v1/docs/readme.md)
Modified: 25.11.04 14:32
Type: Markdown

tokens:  2,145  |  lines:    456  |  words:   1,203  |  chars:  14,892
tks/ln:    4.7  (med: 4)             words/ln:   2.6  (med: 2)
```

**Format Notes**:
- Field order: tokens → lines → words → chars (priority order)
- Fixed-width fields (18 chars per cell) for alignment
- Numbers right-aligned within field
- Lowercase labels for compact, modern look
- Co-located related metrics (tokens/tks/ln, words/words/ln)
- Fits in 90-char terminal width
- Median shown inline to save vertical space

**Note**: Default output is intentionally minimal. Add `-o` or `-d` for structural details.

### Enhanced Output: Outline Flag (`-o` / `--outline`)

**Markdown/Text Files**:
```
Table of Contents:
# Main Heading (Line 5)
  ## Subsection A (Line 23)
    ### Detail A1 (Line 45)
  ## Subsection B (Line 78)
# Another Main (Line 120)
```

**TOC Logic**: Extract all markdown headers (`#`, `##`, `###`, etc.), show hierarchy via indentation, include line numbers for navigation.

**Code Files** (Python example):
```
[Core stats, plus:]

Structure (Functions & Classes):
class SQLiteStorage:
  ├── __init__ (Line 15)
  ├── initialize (Line 28)
  ├── get_db (Line 42)
  └── close (Line 56)

async def create_storage(path: str): (Line 85)

Summary: 5 functions (4 methods, 1 standalone), 1 class
```

**Extraction Rules**:
- **Python**: Use `ast` module for accuracy
- **TypeScript/JavaScript**: Tree-sitter or regex patterns (Phase 2)
- Show hierarchy: classes contain methods
- Include async/sync distinction
- Include type hints if present
- Line numbers for each definition

### Enhanced Output: Dependencies Flag (`-d` / `--deps`)

**Code Files Only** (Python example):
```
[Core stats, plus:]

Dependencies (Internal Only):
from core.storage import SQLiteStorage → ~/projects/muse-v1/core/storage.py
from domain.events import EventManager → ~/projects/muse-v1/domain/events/manager.py

Skipped (Standard/External):
import os, sys, json
from typing import Optional, Dict
import pytest
```

**Resolution Logic**:
- Identify all import statements
- Categorize: internal (project files) vs standard library vs external packages
- Resolve internal imports to actual file paths when possible
- Show path for internal imports, just list external ones

### Multi-File Aggregate Output
```
Analyzed 4 files (Python):

storage.py    1,247 tks    342 lns  [largest]
manager.py      892 tks    256 lns
context.py      654 tks    187 lns
errors.py       234 tks     89 lns  [smallest]

totals (4 files):
tokens:  3,027  |  lines:    874  |  chars:  21,456
```

**Individual File Format**:
- Filename: left-aligned, 14 chars
- Tokens: right-aligned, "N tks" format
- Lines: right-aligned, "N lns" format
- Sorted by token count descending

**Aggregate Format**: Same fixed-width style as single-file output

**Ranking**: Always by token count descending, with `[largest]` and `[smallest]` markers.

### Search Results Output
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

Searched directories (in priority order):
  1. ~/projects/muse-v1/*
  2. ~/projects/* (excluding muse-v1, muse-v0)
  3. ~/.claude/*
  4. ~/projects/muse-v0/*
```

**Search Result Elements**:
- Rank number (directory priority, then date)
- Full path
- Last modified date (format: `YY.MM.DD HH:MM`, 24-hour clock)
- File size (KB, MB)
- Reminder of searched directories at bottom

### Content Search Results
```
Found "EventManager" in 5 files:

[1] ~/projects/muse-v1/domain/events/manager.py (3 matches)
    Line 12: from core.models import EventManager
    Line 45:     manager = EventManager(storage)
    Line 78: class EventManagerError(Exception):

[2] ~/projects/muse-v1/core/storage.py (1 match)
    Line 156:     # Initialize EventManager
    ...

Context: ±2 lines around each match
```

---

## File Type Detection

**Detection Strategy**:
1. Check file extension first (fastest)
2. If ambiguous or no extension, use `file` command
3. If still uncertain, fallback to text analysis

**Type Categories**:

| Extension(s) | Type | Analysis Mode |
|--------------|------|---------------|
| `.md`, `.txt` | Markdown/Text | Text + TOC |
| `.py` | Python | Code + Functions |
| `.ts`, `.tsx`, `.js`, `.jsx` | TypeScript/JS | Code + Functions |
| `.go` | Go | Code (basic for now) |
| `.rs` | Rust | Code (basic for now) |
| `.c`, `.cpp`, `.h`, `.hpp` | C/C++ | Code (basic for now) |
| `.json`, `.yaml`, `.yml` | Config | Text only |
| `.sh`, `.bash` | Shell | Code (basic for now) |

**Ambiguous Cases**:
- `.h` files: Use `file` command to distinguish C vs C++
- Files with code blocks in markdown: Treat as markdown
- Jupyter notebooks (`.ipynb`): JSON analysis + cell count

**Multi-File Type Validation**:
When multiple files provided, all must be same type. Type determined by:
1. All same extension → Use that type
2. Mixed extensions but all code → Generic code analysis
3. Mixed text/code → Error: "Cannot analyze mixed file types. Provide files of same type."

---

## Token Counting Method

**Implementation**: Use existing `count_tokens.py` script from `~/projects/muse-v1/tools/`

**Tokenizer**: [TO BE DETERMINED AFTER REVIEWING EXISTING SCRIPT]
- Likely tiktoken (OpenAI) or Claude tokenizer
- Document which one is used and why

**Batch Processing**: Use `count_tokens_batch.py` if available for multi-file performance

**Edge Cases**:
- Empty files: 0 tokens
- Binary files: Skip or error gracefully
- Very large files (>10MB): Warn and confirm before processing

---

## Command-Line Interface

### Commands & Arguments

```bash
# Analyze (default mode)
filedet <file(s)> [flags]

# Discovery modes
filedet find <pattern>
filedet grep <term> <directory>

# Help
filedet -h, --help
filedet -v, --version
```

### Flags (All Optional)

| Short | Long | Description | Applies To |
|-------|------|-------------|------------|
| `-o` | `--outline` | Show structure (TOC/functions) | Analyze mode |
| `-d` | `--deps` | Show dependencies | Code files only |
| `-h` | `--help` | Show help message | All modes |
| `-v` | `--version` | Show version | All modes |

**Note**: Removed `--json` and `--format` flags per user request (future features).

### Valid Flag Combinations

```bash
# Analyze mode
filedet storage.py              # Core stats only (default)
filedet storage.py -o           # Stats + functions
filedet storage.py -d           # Stats + imports
filedet storage.py -o -d        # Stats + functions + imports
filedet readme.md -o            # Stats + TOC

# Discovery modes (no flags needed)
filedet find storage.py
filedet grep "EventManager" ~/projects/muse-v1

# Help
filedet -h
filedet find -h
filedet grep -h
```

### Invalid Combinations (Auto-Detected Errors)

```bash
# These work - type auto-detected, appropriate analysis applied
filedet readme.md -o            # Markdown → Shows TOC
filedet storage.py -o           # Python → Shows functions
filedet readme.md -d            # Error: deps only for code files
```

### Error Messages

```bash
# Multiple matches found
$ filedet storage.py
Error: Found 3 matches for "storage.py":
  [1] ~/projects/muse-v1/core/storage.py
  [2] ~/projects/muse-v0/core/storage.py
  [3] ~/.claude/examples/storage.py

Provide full path to analyze, or use 'filedet find storage.py' to see all matches.

# Mixed file types
$ filedet file1.py file2.md
Error: Cannot analyze mixed file types.
  file1.py: Python (code)
  file2.md: Markdown (text)
Analyze separately or ensure all files are same type.

# Invalid flag for file type
$ filedet readme.md -d
Error: -d (--deps) flag only applies to code files.
  readme.md is type: Markdown
Try -o (--outline) for table of contents.

# No matches found
$ filedet find nonexistent.py
No matches found for "nonexistent.py"

Searched directories:
  1. ~/projects/muse-v1/*
  2. ~/projects/* (excluding muse-v1, muse-v0)
  3. ~/.claude/*
  4. ~/projects/muse-v0/*
```

---

## Implementation Architecture

### Directory Structure
```
~/projects/general_tools/filedetective/
├── filedet.py                    # CLI entry point, argument parsing
├── config.yaml                   # Configuration file
├── core/
│   ├── __init__.py
│   ├── file_finder.py            # Search with priority logic
│   ├── file_analyzer.py          # Dispatch to type-specific analyzers
│   ├── tokenizer.py              # Wrapper for count_tokens script
│   └── stats_calculator.py       # Mean, median, aggregation
├── analyzers/
│   ├── __init__.py
│   ├── base_analyzer.py          # Abstract base class
│   ├── text_analyzer.py          # Word counts, line stats
│   ├── markdown_analyzer.py      # TOC extraction (-o flag)
│   └── python_analyzer.py        # AST-based extraction (-o and -d flags)
├── utils/
│   ├── __init__.py
│   ├── file_utils.py             # Type detection, date formatting
│   ├── display.py                # Output formatting
│   └── path_resolver.py          # Dependency path resolution
├── tests/
│   ├── test_file_finder.py
│   ├── test_analyzers.py
│   └── fixtures/
│       ├── sample.py
│       ├── sample.md
│       └── sample.txt
├── filedetective-design-and-impl-plan.md  # This document
└── README.md                      # Usage guide
```

**Note**: TypeScript analyzer deferred to Phase 2. Cache manager removed (not needed for MVP).

### Key Modules

#### `file_finder.py`
**Responsibilities**:
- Search directories in priority order
- Handle glob patterns and partial filenames
- Apply exclusion patterns
- Return sorted results (priority, then date)

**API**:
```python
def find_files(
    pattern: str,
    content_search: Optional[str] = None
) -> List[FileMatch]:
    """
    Returns FileMatch objects with:
    - path: str
    - priority: int (1-4)
    - modified_date: datetime
    - size: int (bytes)
    - line_matches: Optional[List[LineMatch]] (for content search)
    """
```

#### `file_analyzer.py`
**Responsibilities**:
- Detect file type
- Dispatch to appropriate analyzer
- Aggregate multi-file results

**API**:
```python
def analyze_file(path: str, flags: AnalysisFlags) -> FileStats:
    """Returns FileStats with all requested metrics"""

def analyze_multiple(paths: List[str], flags: AnalysisFlags) -> AggregateStats:
    """Analyzes multiple files, validates same type, returns aggregate"""
```

#### `python_analyzer.py`
**Responsibilities**:
- Use `ast` module for parsing
- Extract classes, functions, methods
- Build hierarchy tree
- Extract import statements

**API**:
```python
def extract_functions(source: str) -> List[FunctionDef]:
    """Returns function definitions with line numbers"""

def extract_imports(source: str) -> List[ImportDef]:
    """Returns import statements, categorized as internal/external"""
```

**Implementation Note**: Python's `ast` module provides accurate parsing. Example:
```python
import ast

tree = ast.parse(source_code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # Extract function name, line number, decorators
    elif isinstance(node, ast.ClassDef):
        # Extract class structure
```

#### `display.py`
**Responsibilities**:
- Format output with fixed-width fields for alignment
- Handle number formatting (commas for thousands)
- Right-align numbers, left-align labels
- Ensure consistent column widths regardless of number size

**Fixed-Width Field Specifications**:
```
Label field:  8 chars (left-aligned, lowercase)
Number field: 7 chars (right-aligned, comma separators)
Cell total:  18 chars (label + number + spacing)
Separator:   " | " (3 chars)

Example output:
"tokens:  1,247  |  lines:    342  |  chars:   8,934"
         ^^^^^^^^          ^^^^^^^^          ^^^^^^^^
         18 chars          18 chars          18 chars

Field order: tokens, lines, words (text only), chars
```

**Format Functions**:
```python
def format_number(n: int, width: int = 7) -> str:
    """Format number with commas, right-aligned in field."""
    # "  1,247" for n=1247, width=7

def format_stat_line(stats: Dict[str, int]) -> str:
    """Format stats line with fixed-width cells."""
    # Returns: "tokens:  1,247  |  lines:    342  |  chars:   8,934"

def format_rate_line(label: str, mean: float, median: int, width: int = 18) -> str:
    """Format rate line (tks/ln, words/ln) aligned under parent stat."""
    # Returns: "tks/ln:    3.6  (med: 3)"
```

#### `markdown_analyzer.py`
**Responsibilities**:
- Extract headers (`#`, `##`, `###`, etc.)
- Build hierarchical TOC
- Track line numbers

**API**:
```python
def extract_toc(content: str) -> List[TocEntry]:
    """
    Returns TocEntry objects with:
    - level: int (1-6)
    - text: str
    - line_number: int
    """
```

**Implementation Note**: Regex pattern for headers:
```python
pattern = r'^(#{1,6})\s+(.+)$'
```

---

## Open Questions & Design Decisions

### 🔴 Critical Decisions (Need Resolution)

#### 1. Hierarchical Calling Pattern for `-o` Flag
**Question**: What does "hierarchical calling pattern" mean for structure analysis?

**Option A - Structure Only** (EASIER):
```
Show class/function definitions and their containment relationships.
No analysis of which functions call which.
```

**Option B - Call Graph** (HARDER):
```
Show which functions call which other functions.
Requires static analysis or AST traversal to find function calls.
Much more complex, especially for dynamic languages.
```

**Recommendation**: Start with Option A (structure). Option B can be Phase 3 if needed.

#### 2. Dependency Resolution Depth
**Question**: For `-d` flag, how thorough should resolution be?

**Option A - List Only**:
```python
from core.storage import SQLiteStorage
from domain.events import EventManager
```
Just show the import statements as-is.

**Option B - Path Resolution**:
```python
from core.storage import SQLiteStorage → ~/projects/muse-v1/core/storage.py
```
Resolve to actual file paths (requires import system knowledge).

**Option C - Symbol Tracking**:
```python
SQLiteStorage (from core.storage.SQLiteStorage) used on lines: 23, 45, 67
```
Track where imported symbols are used.

**Recommendation**: Start with Option A, add B if path resolution proves valuable. Option C is Phase 3.

#### 3. Token Counting Method
**Question**: Which tokenizer to use?

**Options**:
- tiktoken (OpenAI) - Most common, used by ChatGPT
- anthropic tokenizer - Claude-specific, more accurate for Claude context
- Rough approximation (words * 1.3) - Fast but inaccurate

**Decision**: [TO BE DETERMINED AFTER REVIEWING EXISTING `count_tokens.py`]

#### 4. Content Search Implementation
**Question**: How sophisticated should `filedet grep` be?

**Considerations**:
- Simple string matching: Fast, limited
- Regex support: Powerful, complex syntax
- Fuzzy matching: User-friendly, slower
- File type filtering: Only search specific extensions

**Recommendation**: Start simple (string matching), add regex support in Phase 2 if needed.

### 🟡 Nice-to-Have Questions (Can Defer)

1. **Caching strategy**: SQLite db, JSON files, or no cache?
2. **Color output**: Use libraries like `rich` or just ANSI codes?
3. **Progress bars**: For large searches, show progress?
4. **Config file**: Allow user to customize search directories, exclusions?
5. **Output formats**: Plain text, JSON, what about CSV or HTML?

---

## Phased Implementation Strategy

### Phase 1: Core Functionality (MVP)
**Goal**: Essential analysis with find/grep modes.

**Deliverables**:
- ✅ File search with priority (`filedet find`)
- ✅ Basic stats: tokens, lines, chars, words
- ✅ Date formatting (PST, 24-hour, no AM/PM)
- ✅ File type auto-detection
- ✅ Multi-file comparison with type validation
- ✅ Aggregate stats for multi-file
- ✅ Content search (`filedet grep`)
- ✅ Config file support (`config.yaml`)
- ✅ Help system (`-h` flag)

**Estimated Effort**: 3-4 hours

**Success Criteria**:
```bash
filedet storage.py           # Core stats
filedet find "*.py"          # Lists all Python files
filedet grep "TODO" .        # Searches contents
filedet f1.py f2.py          # Multi-file comparison
```

### Phase 2: Structure Analysis
**Goal**: Add outline and dependency extraction.

**Deliverables**:
- ✅ `-o` flag for markdown (TOC extraction)
- ✅ `-o` flag for Python (functions/classes via AST)
- ✅ `-d` flag for Python (import resolution)
- ✅ Mean/median token calculations (already in Phase 1)

**Estimated Effort**: 2-3 hours (Python only)

**Success Criteria**:
```bash
filedet readme.md -o         # Shows TOC
filedet storage.py -o        # Shows functions/classes
filedet storage.py -d        # Shows imports
filedet storage.py -o -d     # Shows both
```

### Phase 3: Extended Language Support (Future)
**Goal**: Support TypeScript, JavaScript, and other languages.

**Deliverables**:
- ⏸️ TypeScript/JavaScript function extraction
- ⏸️ Go, Rust basic support
- ⏸️ Call graph analysis (if needed)

**Estimated Effort**: +2 hours per language

### Phase 4: Nice-to-Haves (Future)
**Deliverables**:
- ⏸️ JSON output mode (`--json`)
- ⏸️ Format options (`--format table|list|compact`)
- ⏸️ File caching for performance
- ⏸️ Watch mode (monitor file changes)

**Estimated Effort**: TBD

---

## Integration with Existing Scripts

### Reviewed Scripts (Code to Extract)

**1. `/home/kysonk/projects/muse-v1/streams/system/tools/analyze_markdown_notes.py`**
- **Token counting** (lines 21-36): Uses tiktoken with cl100k_base encoding + 1.3x fallback
- **File size formatting** (lines 68-74): Converts bytes → KB/MB/GB human-readable
- **Tokenizer choice**: tiktoken (OpenAI) - consistent across codebase

**2. `/home/kysonk/projects/muse-v1/scripts/muse-codebase-mapper.py`**
- **PythonAnalyzer class** (lines 16-175): Complete AST-based extraction
  - Extracts: classes, methods, functions, async functions, decorators, type hints, properties
  - `_is_method()` helper - prevents double-counting functions inside classes
  - `_get_annotation()` - converts type hints to strings
- **Skip patterns** (lines 193-219): Directories and file patterns to exclude

**3. `/home/kysonk/projects/muse-v1/scripts/v1-import-mapper.py`**
- **Import resolution** (lines 35-38): Converts module path → file path
- **Regex patterns** (lines 16-20): Extract internal imports

**4. `/home/kysonk/projects/muse-v1/scripts/v0-agent-dependency-scanner.py`**
- **Standard library list** (lines 15-27): Filter out stdlib in dependency analysis

### Implementation Decisions

**Tokenizer**: Use **tiktoken (cl100k_base)** as default
- Consistent with existing codebase (3 scripts use it)
- OpenAI vs Claude delta: <5% for most text (comparison incomplete due to API method)
- Fallback: `int(words * 1.3)` when tiktoken unavailable (82.6% accuracy)

**Python Analysis**: **Lift PythonAnalyzer class wholesale**
- Production-ready with edge case handling
- No need to rebuild - adapt existing code
- Already handles async, decorators, properties, type hints

**Code Extraction Pattern**:
```python
# From analyze_markdown_notes.py
import tiktoken

def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except:
        return int(len(text.split()) * 1.3)  # Fallback

def format_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

# From muse-codebase-mapper.py
skip_dirs = {"__pycache__", ".pytest_cache", ".git", "node_modules",
             ".venv", "venv", ".mypy_cache", ".ruff_cache", ".idea", ".vscode"}

# Extract PythonAnalyzer class (lines 16-175) - use as-is
```

---

## Testing Strategy

### Unit Tests
- `test_file_finder.py`: Search, prioritization, sorting
- `test_type_detection.py`: File type identification
- `test_analyzers.py`: Each analyzer independently
- `test_stats.py`: Mean, median, aggregation calculations

### Integration Tests
- End-to-end CLI invocations
- Multi-file scenarios
- Error handling (missing files, invalid flags)

### Test Fixtures
Create sample files in `tests/fixtures/`:
```
fixtures/
├── sample.py        # Python with classes, functions
├── sample.ts        # TypeScript
├── sample.md        # Markdown with headers
├── sample.txt       # Plain text
└── empty.py         # Edge case: empty file
```

### Manual Testing Checklist
```bash
# Basic stats
filedet fixtures/sample.py

# Discovery
filedet find "sample.py"

# Multi-file
filedet fixtures/*.py

# Flags
filedet fixtures/sample.md -o        # TOC
filedet fixtures/sample.py -o        # Functions
filedet fixtures/sample.py -d        # Dependencies

# Errors
filedet nonexistent.py               # Should error gracefully
filedet sample.py sample.md          # Mixed types should error
```

---

## Performance Considerations

### Search Performance
**Problem**: Recursive search across large directories can be slow.

**Solutions**:
1. **Parallel search**: Use `multiprocessing` to search directories concurrently
2. **Early termination**: Stop after finding unique match (when not `--search-only`)
3. **Cache index**: Build file index, update incrementally
4. **Respect exclusions**: Skip `.git`, `node_modules` early

**Benchmark Target**: <1 second for typical search across all directories

### Analysis Performance
**Problem**: Large files (>10K lines) take time to analyze.

**Solutions**:
1. **Streaming analysis**: Don't load entire file into memory
2. **Lazy analysis**: Only compute requested metrics
3. **Batch token counting**: Use batch script for multi-file

**Benchmark Target**: <2 seconds for typical file analysis

### Memory Considerations
**Problem**: Multi-file analysis could consume significant memory.

**Solutions**:
1. **Incremental processing**: Analyze one file at a time, accumulate stats
2. **Limit file size**: Warn on files >10MB, require `--force` flag
3. **Streaming for content search**: Use generators, not loading all results

---

## Error Handling & Edge Cases

### File System Errors
- **Permission denied**: Skip with warning, continue search
- **Broken symlinks**: Skip with warning
- **File deleted during analysis**: Graceful error message

### Analysis Errors
- **Binary file**: Detect early, show "Cannot analyze binary file"
- **Encoding errors**: Try UTF-8, fall back to latin-1, then error
- **Parsing errors**: Show line number where parsing failed
- **Empty file**: Show 0 for all metrics, don't error

### User Input Errors
- **No matches found**: Clear message, suggest `filedet find <pattern>`
- **Ambiguous matches**: List all, suggest full path or `filedet find`
- **Invalid flag combo**: Explain why invalid, suggest correct usage
- **Mixed file types**: List types found, explain restriction

### Validation Rules
```python
# Before analysis
if multiple_files:
    if not all_same_type(files):
        error("Mixed file types")

if is_text_file(file) and "-d" in flags:
    error("-d (--deps) only for code files")

# Note: -o flag works for both code and text (shows functions or TOC respectively)
```

---

## Future Enhancements (Backlog)

### P1 - High Value
- Content search with line context
- TypeScript/JavaScript function extraction
- Dependency path resolution
- Output to JSON for scripting

### P2 - Nice to Have
- Compare mode (side-by-side file comparison)
- Watch mode (monitor file changes)
- Export reports (HTML, PDF)
- Plugin system for custom analyzers

### P3 - Low Priority
- GUI wrapper (if CLI proves popular)
- VS Code extension
- Git integration (blame, history)
- Syntax highlighting in output

---

## Development Notes for Next Session

### Before Starting Implementation
1. **Review existing token counting scripts** - Update "Integration with Existing Scripts" section
2. **Clarify open questions** - Get user input on critical decisions
3. **Set up project structure** - Create directories, init files
4. **Create test fixtures** - Sample files for testing

### Implementation Order
1. Start with `file_finder.py` - Core search logic
2. Then `file_analyzer.py` - Type detection and dispatch
3. Then `tokenizer.py` - Integrate existing scripts
4. Then individual analyzers - Start with text, then Python
5. Finally `filedet.py` - CLI entry point and argument parsing

### Testing Strategy
- Write tests alongside implementation (TDD)
- Manual test frequently with real files
- Test edge cases early (empty files, permission errors, etc.)

### Git Workflow
- Commit after each module completion
- Tag milestones (Phase 1 complete, etc.)
- Push regularly to avoid loss

---

## Resolved Design Decisions

### Command Structure
✅ **Action-oriented** (not type-based): `filedet <file>`, `filedet find`, `filedet grep`
✅ **Auto-detection** replaces type modes - no need to specify code vs docs
✅ **Shortened command**: `filedet` (not `filedetective`)
✅ **Config location**: `~/projects/general_tools/filedetective/config.yaml`

### Flags
✅ **Minimal flag set**: `-o` (outline), `-d` (deps), `-h` (help), `-v` (version)
✅ **No JSON output** (future feature)
✅ **No format flag** (future feature)
✅ **Short + long flags**: `-o` and `--outline` both work

### Default Behavior
✅ **Core stats only**: Tokens, lines, chars, words, mean/median
✅ **Structure on demand**: Add `-o` for TOC/functions
✅ **Dependencies on demand**: Add `-d` for imports (code only)

## Open Questions for Next Session

1. **Hierarchical calling pattern** for `-o`: Structure only (Option A - RECOMMENDED) or call graph (Option B)?
2. **Dependency resolution** for `-d`: List imports (A - RECOMMENDED), resolve paths (B), or track usage (C)?
3. **Output styling**: Plain text or use `rich` library for colors/tables?
4. **Content search depth**: How many lines of context around matches?

## Resolved Questions

✅ **Token counting**: Use tiktoken (cl100k_base) with 1.3x word fallback - consistent with codebase
✅ **Python analysis**: Lift PythonAnalyzer from muse-codebase-mapper.py (production-ready)
✅ **Skip patterns**: Use existing patterns from muse-codebase-mapper.py

## Session Boundary Notes

**Context to recover**:
- This tool emerged from desire to quickly analyze files across muse-v1, muse-v0, and .claude
- User has existing `count_tokens.py` scripts to integrate (not yet reviewed)
- Design happened in conversation, this spec captures complete state
- Next session should start by reviewing existing scripts, then update this spec before coding

**Files to reference next session**:
- This spec: `~/projects/general_tools/filedetective-design-and-impl-plan.md`
- Token scripts: `~/projects/muse-v1/tools/count_tokens*.py`
- Priority search dirs: muse-v1 (P1), general projects (P2), .claude (P3), muse-v0 (P4)

---

**End of Specification v1.1**
