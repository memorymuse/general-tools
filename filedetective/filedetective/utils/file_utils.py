"""File utility functions for type detection and formatting."""
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class FileType(Enum):
    """File type categories."""
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    MARKDOWN = "Markdown"
    TEXT = "Text"
    JSON = "JSON"
    YAML = "YAML"
    SHELL = "Shell"
    GO = "Go"
    RUST = "Rust"
    C = "C"
    CPP = "C++"
    UNKNOWN = "Unknown"

    @property
    def is_code(self) -> bool:
        """Check if this is a code file type."""
        return self in {
            FileType.PYTHON,
            FileType.JAVASCRIPT,
            FileType.TYPESCRIPT,
            FileType.GO,
            FileType.RUST,
            FileType.C,
            FileType.CPP,
            FileType.SHELL,
        }

    @property
    def is_text(self) -> bool:
        """Check if this is a text/documentation file type."""
        return self in {
            FileType.MARKDOWN,
            FileType.TEXT,
        }


# Extension to file type mapping
EXTENSION_MAP = {
    ".py": FileType.PYTHON,
    ".js": FileType.JAVASCRIPT,
    ".jsx": FileType.JAVASCRIPT,
    ".ts": FileType.TYPESCRIPT,
    ".tsx": FileType.TYPESCRIPT,
    ".md": FileType.MARKDOWN,
    ".txt": FileType.TEXT,
    ".json": FileType.JSON,
    ".yaml": FileType.YAML,
    ".yml": FileType.YAML,
    ".sh": FileType.SHELL,
    ".bash": FileType.SHELL,
    ".go": FileType.GO,
    ".rs": FileType.RUST,
    ".c": FileType.C,
    ".h": FileType.C,
    ".cpp": FileType.CPP,
    ".hpp": FileType.CPP,
    ".cc": FileType.CPP,
    ".cxx": FileType.CPP,
}


def detect_file_type(file_path: str) -> FileType:
    """Detect file type from extension.

    Args:
        file_path: Path to file

    Returns:
        Detected FileType
    """
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext, FileType.UNKNOWN)


def format_date(timestamp: float, fmt: str = "%y.%m.%d %H:%M") -> str:
    """Format timestamp to human-readable date.

    Args:
        timestamp: Unix timestamp
        fmt: Date format string (default: YY.MM.DD HH:MM)

    Returns:
        Formatted date string
    """
    return datetime.fromtimestamp(timestamp).strftime(fmt)


def get_file_stats(file_path: str) -> dict:
    """Get basic file statistics.

    Args:
        file_path: Path to file

    Returns:
        Dict with size, modified time, type
    """
    stat = os.stat(file_path)
    return {
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "type": detect_file_type(file_path),
    }


def validate_file_types(file_paths: list[str]) -> tuple[bool, Optional[str]]:
    """Validate that all files are the same type category.

    Args:
        file_paths: List of file paths

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_paths:
        return True, None

    types = [detect_file_type(fp) for fp in file_paths]

    # Check if all are code
    all_code = all(t.is_code for t in types)
    # Check if all are text
    all_text = all(t.is_text for t in types)

    if all_code or all_text or len(set(types)) == 1:
        return True, None

    # Mixed types - generate error message
    type_list = "\n".join(
        f"  {Path(fp).name}: {t.value} ({'code' if t.is_code else 'text'})"
        for fp, t in zip(file_paths, types)
    )
    return False, f"Cannot analyze mixed file types.\n{type_list}\nAnalyze separately or ensure all files are same type."


def should_skip(path: str, skip_dirs: set[str], skip_patterns: list[str]) -> bool:
    """Check if path should be skipped during search.

    Args:
        path: Path to check
        skip_dirs: Set of directory names to skip
        skip_patterns: List of file patterns to skip

    Returns:
        True if path should be skipped
    """
    path_obj = Path(path)

    # Check if any parent directory is in skip list
    for part in path_obj.parts:
        if part in skip_dirs:
            return True

    # Check if filename matches any skip pattern
    import fnmatch
    for pattern in skip_patterns:
        if fnmatch.fnmatch(path_obj.name, pattern):
            return True

    return False
