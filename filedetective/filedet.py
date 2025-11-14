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
from utils.display import (
    display_single_file,
    display_multiple_files,
    display_search_results,
    display_error,
)


VERSION = "0.1.0"


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

    else:
        # Analyze mode (default)
        return handle_analyze(
            args.files_or_command,
            args.outline,
            args.deps
        )


if __name__ == "__main__":
    sys.exit(main())
