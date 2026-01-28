#!/usr/bin/env python3
"""
FileDetective CLI - Intelligent file discovery and analysis.

Supports auto-search with wildcards and path-based pattern matching.

Usage:
    filedet <file(s)> [flags]        # Analyze files (auto-searches if not found)
    filedet <pattern> [flags]        # Path-based patterns: "cc-*/drafts/*.md"
    filedet find <pattern>           # Find files without analyzing
    filedet grep <term> <dir>        # Search file contents
"""
import sys
import argparse
import re
from pathlib import Path
from typing import Optional, Tuple

from .core.file_finder import FileFinder
from .core.file_analyzer import FileAnalyzer
from .core.history import HistoryFinder
from .utils.display import (
    display_single_file,
    display_multiple_files,
    display_search_results,
    display_history_table,
    display_history_full,
    display_error,
)


VERSION = "0.2.0"


def parse_file_with_range(file_arg: str) -> Tuple[str, Optional[int], Optional[int]]:
    """Parse a file argument that may include a line range.

    Supported formats:
        file.py         → (file.py, None, None)     # Full file
        file.py:10-50   → (file.py, 10, 50)         # Lines 10-50
        file.py:10-     → (file.py, 10, None)       # Line 10 to end
        file.py:-50     → (file.py, None, 50)       # Start to line 50

    Args:
        file_arg: File path, optionally with :start-end suffix

    Returns:
        Tuple of (file_path, line_start, line_end)
        line_start/line_end are 1-indexed and inclusive, or None
    """
    # Match pattern: path:start-end where start and end are optional
    match = re.match(r'^(.+):(\d*)-(\d*)$', file_arg)
    if match:
        file_path = match.group(1)
        start_str = match.group(2)
        end_str = match.group(3)

        line_start = int(start_str) if start_str else None
        line_end = int(end_str) if end_str else None

        # Validate: if both provided, start must be <= end
        if line_start is not None and line_end is not None and line_start > line_end:
            raise ValueError(f"Invalid range: start ({line_start}) > end ({line_end})")

        return file_path, line_start, line_end

    # No range specified
    return file_arg, None, None


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="filedet",
        description="FileDetective - Intelligent file discovery and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze files (auto-searches if not found locally)
  filedet storage                 # Find and analyze storage files
  filedet storage.py -o           # Show structure (see below)
  filedet storage.py -o -d        # Show structure + dependencies

  # The -o flag extracts structure based on file type:
  #   Markdown: Heading hierarchy as navigable TOC (# → ## → ###)
  #   Python:   Classes, methods, functions with line numbers (AST-parsed)
  #   JS/TS:    Functions, classes, exports (regex-based, ~90% coverage)
  #   Other:    Skipped silently (no error, just omits structure)

  # Line ranges (count tokens for specific lines)
  filedet file.py:10-50           # Lines 10-50 only
  filedet file.py:100-            # Line 100 to end
  filedet file.py:-50             # Start to line 50
  filedet a.py:10-50 b.py:20-30   # Multi-file with ranges

  # Multiple files
  filedet *.py                    # Analyze all Python files in current dir
  filedet file1.py file2.py       # Analyze specific files

  # Analyze directories
  filedet ./src                   # All files in src/ (non-recursive)
  filedet ./src -r                # Recursive (include subdirectories)
  filedet ./src -r -ft .py .md    # Recursive, filter by extension

  # Path-based patterns (use / for directory matching)
  filedet "cc-*/drafts/*.md"      # Files in cc-* directories
  filedet "*/memos/design/*.md"   # Across all subdirectories

  # Commands
  filedet find storage.py         # Find in configured project directories
  filedet find storage.py -l      # Find in current directory (local)
  filedet find docs/*.md docs/*.py # Multiple patterns at once
  filedet grep "TODO" .           # Search file contents

  # History (recent files)
  filedet hist                    # 15 most recent files in cwd
  filedet hist -n 30              # Adjust count
  filedet hist -ft .md .py        # Filter by file type
  filedet hist -g                 # Show git status column
  filedet hist -gd                # Show git status + last commit
  filedet hist -h                 # Show hist command help
        """
    )

    parser.add_argument(
        "files_or_command",
        nargs="+",
        help="Files to analyze, or command (find/grep)"
    )

    parser.add_argument(
        "-o", "--outline",
        action="store_true",
        help="Show file structure: Markdown→heading TOC, Python→classes/functions (AST), JS/TS→functions/exports (regex)"
    )

    parser.add_argument(
        "-d", "--deps",
        action="store_true",
        help="Show dependencies (code files only)"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )

    parser.add_argument(
        "-l", "--local",
        action="store_true",
        help="Search current directory instead of configured project directories"
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Include subdirectories when analyzing a directory"
    )

    parser.add_argument(
        "-ft", "--filetypes",
        nargs="+",
        metavar="EXT",
        help="Filter by file extension(s) when analyzing a directory (e.g., .py .md)"
    )

    return parser


def handle_find(patterns: list[str], local: bool = False) -> int:
    """Handle find command.

    Args:
        patterns: One or more patterns to search for
        local: If True, search current directory instead of configured dirs

    Returns:
        Exit code
    """
    from .core.file_finder import FileMatch

    finder = FileFinder()
    local_dir = Path.cwd() if local else None

    # Collect all matches from all patterns
    all_matches = []
    for pattern in patterns:
        # First, check if this "pattern" is actually an existing file
        # This handles shell expansion: `filedet find *SELF-REVIEW*` expands
        # to `filedet find SELF-REVIEW-PROTOCOL-ANALYSIS.md` if that file exists
        pattern_path = Path(pattern).expanduser()
        if pattern_path.exists() and pattern_path.is_file():
            # It's an existing file - return it directly
            stat = pattern_path.stat()
            all_matches.append(FileMatch(
                path=str(pattern_path.resolve()),
                priority=0,
                modified_date=stat.st_mtime,
                size=stat.st_size
            ))
            continue

        matches = finder.find_files(pattern, local_dir=local_dir)
        all_matches.extend(matches)

    # Remove duplicates (same file matched by multiple patterns)
    seen = set()
    unique_matches = []
    for match in all_matches:
        if match.path not in seen:
            seen.add(match.path)
            unique_matches.append(match)

    # Sort by recency
    unique_matches.sort(key=lambda m: m.modified_date, reverse=True)

    display_search_results(unique_matches, patterns)
    return 0 if unique_matches else 1


def handle_grep(term: str, directory: str) -> int:
    """Handle grep command.

    Args:
        term: Search term
        directory: Directory to search

    Returns:
        Exit code
    """
    # Expand directory path
    dir_path = Path(directory).expanduser().resolve()

    if not dir_path.exists():
        display_error(f"Directory not found: {directory}")
        return 1

    if not dir_path.is_dir():
        display_error(f"Not a directory: {directory}")
        return 1

    # Find files with content
    finder = FileFinder()
    matches = finder.find_files("*", content_search=term)

    # Filter to only files in target directory
    matches = [m for m in matches if str(dir_path) in m.path]

    if matches:
        print(f"\nFound \"{term}\" in {len(matches)} files:\n")
        for i, match in enumerate(matches, 1):
            print(f"[{i}] {match.display_path}")
        print()
        return 0
    else:
        print(f"\nNo matches found for \"{term}\" in {directory}\n")
        return 1


HIST_HELP = """usage: filedet hist [directory] [-n COUNT] [-ft EXT [EXT ...]] [-g] [-gd] [-full]

Show recently modified files in a directory tree.

positional arguments:
  directory             Directory to search (default: current directory)

optional arguments:
  -h, --help            Show this help message and exit
  -n, --count COUNT     Number of files to show (default: 15)
  -ft, --filetypes EXT [EXT ...]
                        Filter by file extension(s). Accepts: .md, md, *.env*, *local
  -g, --git             Show git status column (M=modified, A=staged, ?=untracked, ✓=clean)
  -gd, --git-detail     Show git status + last commit info
  -full, --full         Simple output: datetime + full path only (no table)

Examples:
  filedet hist                      # 15 recent in current directory
  filedet hist ~/projects -n 10     # 10 recent in specific directory
  filedet hist -ft .md .py          # Only markdown and python files
  filedet hist -ft .env* .*local    # Dotfiles matching patterns
  filedet hist -g                   # Include git status column
  filedet hist -gd                  # Include git status + last commit
  filedet hist -full                # Simple datetime + full path output
"""


def handle_hist(args: list[str]) -> int:
    """Handle hist command.

    Args:
        args: Arguments after 'hist' (e.g., ['-n', '30', '-ft', '.md'])

    Returns:
        Exit code
    """
    # Check for help flag
    if '-h' in args or '--help' in args:
        print(HIST_HELP)
        return 0

    # Parse arguments
    directory = "."
    count = 15
    filetypes = None
    git_status = False
    git_detail = False
    full_output = False

    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ('-n', '--count'):
            if i + 1 >= len(args):
                display_error("-n requires a number")
                return 1
            try:
                count = int(args[i + 1])
            except ValueError:
                display_error(f"-n requires a number, got: {args[i + 1]}")
                return 1
            i += 2

        elif arg in ('-ft', '--filetypes'):
            # Collect all following arguments until next flag or end
            filetypes = []
            i += 1
            while i < len(args) and not args[i].startswith('-'):
                filetypes.append(args[i])
                i += 1
            if not filetypes:
                display_error("-ft requires at least one file type")
                return 1

        elif arg in ('-g', '--git'):
            git_status = True
            i += 1

        elif arg in ('-gd', '--git-detail'):
            git_detail = True
            i += 1

        elif arg in ('-full', '--full'):
            full_output = True
            i += 1

        elif arg.startswith('-'):
            display_error(f"Unknown flag: {arg}")
            print("Use 'filedet hist -h' for help")
            return 1

        else:
            # Positional argument = directory
            directory = arg
            i += 1

    # Expand directory path
    dir_path = Path(directory).expanduser().resolve()

    if not dir_path.exists():
        display_error(f"Directory not found: {directory}")
        return 1

    if not dir_path.is_dir():
        display_error(f"Not a directory: {directory}")
        return 1

    # Find recent files
    finder = HistoryFinder()
    entries = finder.find_recent(
        dir_path,
        count=count,
        filetypes=filetypes,
        git_status=git_status or git_detail,
        git_detail=git_detail
    )

    if entries:
        if full_output:
            display_history_full(entries, dir_path)
        else:
            display_history_table(entries, dir_path, show_git=git_status or git_detail, show_git_detail=git_detail)
        return 0
    else:
        if filetypes:
            print(f"\nNo files matching {filetypes} found in {directory}\n")
        else:
            print(f"\nNo files found in {directory}\n")
        return 1


def enumerate_directory_files(
    directory: Path,
    recursive: bool = False,
    filetypes: Optional[list[str]] = None
) -> list[str]:
    """Enumerate files in a directory for analysis.

    Args:
        directory: Directory to enumerate
        recursive: If True, include subdirectories
        filetypes: Optional list of extensions to filter by (e.g., [".md", "py"])

    Returns:
        List of absolute file paths, sorted by modification time (most recent first)
    """
    from .core.history import HistoryFinder
    import fnmatch

    finder = HistoryFinder()
    files_found = []

    # Normalize filetype patterns for matching
    normalized_filetypes = None
    if filetypes:
        normalized_filetypes = [finder._normalize_extension(ft) for ft in filetypes]

    if recursive:
        # Use os.walk for recursive traversal
        import os
        for root, dirs, files in os.walk(directory, followlinks=False):
            # Filter out skip directories in-place
            dirs[:] = [d for d in dirs if not finder._should_skip_dir(d)]

            for filename in files:
                file_path = Path(root) / filename

                # Skip files that should be skipped
                if finder._should_skip_file(filename):
                    continue

                # Check filetype filter
                if normalized_filetypes and not finder._matches_filetypes(filename, normalized_filetypes):
                    continue

                # Only include readable files
                if file_path.is_file():
                    files_found.append(file_path)
    else:
        # Non-recursive: only top-level files
        for item in directory.iterdir():
            if not item.is_file():
                continue

            filename = item.name

            # Skip files that should be skipped
            if finder._should_skip_file(filename):
                continue

            # Check filetype filter
            if normalized_filetypes and not finder._matches_filetypes(filename, normalized_filetypes):
                continue

            files_found.append(item)

    # Sort by modification time (most recent first)
    files_found.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(f.resolve()) for f in files_found]


def _find_case_insensitive_local(pattern: str) -> Optional[Path]:
    """Find a file in current directory with case-insensitive matching.

    Args:
        pattern: Filename to search for (may include ./ prefix)

    Returns:
        Path to matching file if found, None otherwise
    """
    # Strip ./ prefix if present
    filename = pattern.lstrip('./')
    filename_lower = filename.lower()

    for item in Path.cwd().iterdir():
        if item.is_file() and item.name.lower() == filename_lower:
            return item
    return None


def _has_extension(pattern: str) -> bool:
    """Check if pattern has a file extension.

    Args:
        pattern: Filename or pattern to check

    Returns:
        True if has an extension like .py, .md, etc.
    """
    # Get just the filename part (strip any directory prefix)
    name = Path(pattern).name
    # Check for extension: has a dot, and something after it that's not a wildcard
    if '.' in name:
        suffix = name.rsplit('.', 1)[-1]
        # It's an extension if it's alphanumeric (not a wildcard pattern)
        return suffix.isalnum()
    return False


def handle_analyze(files: list[str], show_outline: bool, show_deps: bool, local: bool = False, recursive: bool = False, filetypes: Optional[list[str]] = None) -> int:
    """Handle file analysis.

    Args:
        files: List of file paths or directories (optionally with :start-end line ranges)
        show_outline: Show structure
        show_deps: Show dependencies
        local: If True, search current directory instead of configured dirs
        recursive: If True, include subdirectories when analyzing directories
        filetypes: Optional list of extensions to filter by (for directory analysis)

    Returns:
        Exit code
    """
    analyzer = FileAnalyzer()
    finder = FileFinder()
    local_dir = Path.cwd() if local else None

    # Resolve file paths - stores tuples of (path, line_start, line_end)
    resolved_files: list[Tuple[str, Optional[int], Optional[int]]] = []

    for file_arg in files:
        # Parse potential line range (e.g., file.py:10-50)
        try:
            file_pattern, line_start, line_end = parse_file_with_range(file_arg)
        except ValueError as e:
            display_error(str(e))
            return 1

        file_path = Path(file_pattern).expanduser()

        # Check if pattern explicitly references current directory
        is_explicit_local = file_pattern.startswith('./') or file_pattern.startswith('.\\')

        if file_path.exists():
            # Check if it's a directory (use filesystem check, not heuristics)
            if file_path.is_dir():
                # Line ranges don't apply to directories
                if line_start is not None or line_end is not None:
                    display_error(f"Line ranges not supported for directories: {file_arg}")
                    return 1
                # Enumerate files from directory
                dir_files = enumerate_directory_files(file_path, recursive=recursive, filetypes=filetypes)
                if not dir_files:
                    filter_msg = f" matching {filetypes}" if filetypes else ""
                    display_error(f"No files found in directory{filter_msg}: {file_pattern}")
                    return 1
                # Directory files get no line range
                resolved_files.extend((f, None, None) for f in dir_files)
            else:
                # It's a file (could be extensionless like a Unix script)
                resolved_files.append((str(file_path.resolve()), line_start, line_end))
        elif is_explicit_local:
            # Explicit local path (./) - only search locally with case-insensitive matching
            local_match = _find_case_insensitive_local(file_pattern)
            if local_match:
                resolved_files.append((str(local_match.resolve()), line_start, line_end))
            else:
                display_error(f"No files found matching: {file_pattern}")
                return 1
        else:
            # File doesn't exist locally - try case-insensitive local match first
            local_match = _find_case_insensitive_local(file_pattern)
            if local_match:
                resolved_files.append((str(local_match.resolve()), line_start, line_end))
                continue

            # Not found locally - search in configured directories
            # Detect if wildcards are present
            has_wildcard = '*' in file_pattern or '?' in file_pattern
            has_ext = _has_extension(file_pattern)

            # Patterns with extensions but no wildcards are treated as specific files
            # Only search configured dirs if user explicitly uses wildcards or fuzzy names
            if has_ext and not has_wildcard:
                # Specific file with extension - don't auto-search everywhere
                display_error(
                    f"File not found: {file_pattern}\n"
                    f"Use 'filedet find {file_pattern}' to search all configured directories."
                )
                return 1

            if has_wildcard:
                # Use pattern as-is (finder will handle it with case-insensitive matching)
                search_pattern = file_pattern
            else:
                # No extension/wildcard - wrap in wildcards for fuzzy matching
                search_pattern = f"*{file_pattern}*"

            matches = finder.find_files(search_pattern, local_dir=local_dir)

            # Sort by recency (most recent first)
            matches.sort(key=lambda m: m.modified_date, reverse=True)

            if len(matches) == 0:
                display_error(f"No files found matching: {file_pattern}")
                return 1
            elif len(matches) == 1:
                # Single match - analyze it (preserve any line range from original arg)
                resolved_files.append((matches[0].path, line_start, line_end))
            else:
                # Multiple matches - show options sorted by recency
                display_error(
                    f"Found {len(matches)} matches for \"{file_pattern}\".\n"
                    f"Showing most recent first. Provide full path or more specific name to analyze."
                )
                from .utils.file_utils import format_date
                for i, match in enumerate(matches[:10], 1):
                    print(f"  [{i}] {match.display_path}")
                    print(f"      Modified: {format_date(match.modified_date)}")
                if len(matches) > 10:
                    print(f"  ... and {len(matches) - 10} more")
                print()
                return 1

    # Analyze
    try:
        if len(resolved_files) == 1:
            # Single file
            file_path, line_start, line_end = resolved_files[0]
            stats = analyzer.analyze_file(
                file_path,
                show_outline=show_outline,
                show_deps=show_deps,
                line_start=line_start,
                line_end=line_end
            )
            display_single_file(stats)
        else:
            # Multiple files
            agg_stats = analyzer.analyze_multiple(
                resolved_files,
                show_outline=show_outline,
                show_deps=show_deps
            )
            display_multiple_files(agg_stats)

        return 0

    except Exception as e:
        display_error(str(e))
        return 1


def main():
    """Main entry point."""
    # Handle 'hist' command before argparse (so hist -h works)
    if len(sys.argv) > 1 and sys.argv[1] == "hist":
        return handle_hist(sys.argv[2:])

    parser = create_parser()
    args = parser.parse_args()

    # Check if it's a command
    first_arg = args.files_or_command[0]

    if first_arg == "find":
        if len(args.files_or_command) < 2:
            display_error("find command requires at least one pattern")
            print("Usage: filedet find <pattern> [<pattern2> ...] [-l]")
            return 1
        patterns = args.files_or_command[1:]  # All args after "find"
        return handle_find(patterns, local=args.local)

    elif first_arg == "grep":
        if len(args.files_or_command) < 3:
            display_error("grep command requires term and directory")
            print("Usage: filedet grep <term> <directory>")
            return 1
        term = args.files_or_command[1]
        directory = args.files_or_command[2]
        return handle_grep(term, directory)

    elif first_arg == "hist":
        # Pass remaining args to hist handler
        return handle_hist(args.files_or_command[1:])

    else:
        # Analyze mode (default)
        return handle_analyze(
            args.files_or_command,
            args.outline,
            args.deps,
            local=args.local,
            recursive=args.recursive,
            filetypes=args.filetypes
        )


if __name__ == "__main__":
    sys.exit(main())
