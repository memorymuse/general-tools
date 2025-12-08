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
from pathlib import Path

from core.file_finder import FileFinder
from core.file_analyzer import FileAnalyzer
from core.history import HistoryFinder
from utils.display import (
    display_single_file,
    display_multiple_files,
    display_search_results,
    display_history_table,
    display_error,
)


VERSION = "0.2.0"


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
  filedet storage.py -o           # Show structure
  filedet storage.py -o -d        # Show structure + dependencies

  # Multiple files
  filedet *.py                    # Analyze all Python files in current dir
  filedet file1.py file2.py       # Analyze specific files

  # Path-based patterns (use / for directory matching)
  filedet "cc-*/drafts/*.md"      # Files in cc-* directories
  filedet "*/memos/design/*.md"   # Across all subdirectories

  # Commands
  filedet find storage.py         # Find all matches (no analysis)
  filedet find docs/*.md docs/*.py # Multiple patterns at once
  filedet grep "TODO" .           # Search file contents

  # History (recent files)
  filedet hist                    # 15 most recent files in cwd
  filedet hist -n 30              # Adjust count
  filedet hist -ft .md .py        # Filter by file type
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
        help="Show structure (TOC for text, functions for code)"
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

    return parser


def handle_find(patterns: list[str]) -> int:
    """Handle find command.

    Args:
        patterns: One or more patterns to search for

    Returns:
        Exit code
    """
    finder = FileFinder()

    # Collect all matches from all patterns
    all_matches = []
    for pattern in patterns:
        matches = finder.find_files(pattern)
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


HIST_HELP = """usage: filedet hist [directory] [-n COUNT] [-ft EXT [EXT ...]]

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
    entries = finder.find_recent(dir_path, count=count, filetypes=filetypes)

    if entries:
        display_history_table(entries, dir_path)
        return 0
    else:
        if filetypes:
            print(f"\nNo files matching {filetypes} found in {directory}\n")
        else:
            print(f"\nNo files found in {directory}\n")
        return 1


def handle_analyze(files: list[str], show_outline: bool, show_deps: bool) -> int:
    """Handle file analysis.

    Args:
        files: List of file paths
        show_outline: Show structure
        show_deps: Show dependencies

    Returns:
        Exit code
    """
    analyzer = FileAnalyzer()
    finder = FileFinder()

    # Resolve file paths
    resolved_files = []
    for file_pattern in files:
        file_path = Path(file_pattern).expanduser()

        if file_path.exists():
            # Direct path
            resolved_files.append(str(file_path))
        else:
            # File doesn't exist locally - search for it
            # Detect if wildcards are present
            has_wildcard = '*' in file_pattern or '?' in file_pattern

            if has_wildcard:
                # Use pattern as-is
                search_pattern = file_pattern
            else:
                # Wrap in wildcards for fuzzy matching
                search_pattern = f"*{file_pattern}*"

            matches = finder.find_files(search_pattern)

            # Sort by recency (most recent first)
            matches.sort(key=lambda m: m.modified_date, reverse=True)

            if len(matches) == 0:
                display_error(f"No files found matching: {file_pattern}")
                return 1
            elif len(matches) == 1:
                # Single match - analyze it
                resolved_files.append(matches[0].path)
            else:
                # Multiple matches - show options sorted by recency
                display_error(
                    f"Found {len(matches)} matches for \"{file_pattern}\".\n"
                    f"Showing most recent first. Provide full path or more specific name to analyze."
                )
                from utils.file_utils import format_date
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
            stats = analyzer.analyze_file(
                resolved_files[0],
                show_outline=show_outline,
                show_deps=show_deps
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
            print("Usage: filedet find <pattern> [<pattern2> ...]")
            return 1
        patterns = args.files_or_command[1:]  # All args after "find"
        return handle_find(patterns)

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
            args.deps
        )


if __name__ == "__main__":
    sys.exit(main())
