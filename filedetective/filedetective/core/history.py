"""History finder for recently modified files."""
import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .tokenizer import count_tokens


@dataclass
class HistoryEntry:
    """A file entry with modification metadata."""
    path: str              # Absolute path
    relative_path: str     # Relative to search root
    modified_date: float   # Unix timestamp
    extension: str         # File extension (e.g., ".py")
    lines: int
    tokens: int
    # Git info (optional)
    git_status: Optional[str] = None           # M, A, ?, ✓, !, -
    git_commit_relative: Optional[str] = None  # "2d", "5h"
    git_commit_msg: Optional[str] = None       # Truncated commit message


# Utility dotfiles to include (even though they start with .)
UTILITY_DOTFILE_PATTERNS = [
    ".gitignore",
    ".gitattributes",
    ".env",
    ".env*",
    ".claude*",
    ".*local",
    ".editorconfig",
    ".prettierrc*",
    ".eslintrc*",
    ".nvmrc",
    ".python-version",
    ".tool-versions",
    ".dockerignore",
]

# Additional skip patterns for history (beyond config.yaml)
HISTORY_SKIP_PATTERNS = [
    "*.db-wal",
    "*.db-shm",
    "*.lock",
    ".coverage",
    "*.egg-info",
    "*.log",
]

# Directories to always skip
HISTORY_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
    "dist",
    "build",
    "*.egg-info",
}


class HistoryFinder:
    """Finds recently modified files in a directory tree."""

    def __init__(self, skip_dirs: Optional[set[str]] = None, skip_patterns: Optional[list[str]] = None):
        """Initialize history finder.

        Args:
            skip_dirs: Additional directories to skip (merged with defaults)
            skip_patterns: Additional file patterns to skip (merged with defaults)
        """
        self.skip_dirs = HISTORY_SKIP_DIRS.copy()
        if skip_dirs:
            self.skip_dirs.update(skip_dirs)

        self.skip_patterns = list(HISTORY_SKIP_PATTERNS)
        if skip_patterns:
            self.skip_patterns.extend(skip_patterns)

    def find_recent(
        self,
        directory: Path,
        count: int = 15,
        filetypes: Optional[list[str]] = None,
        git_status: bool = False,
        git_detail: bool = False
    ) -> list[HistoryEntry]:
        """Find most recently modified files.

        Args:
            directory: Directory to search (recursive)
            count: Maximum number of results
            filetypes: Optional list of extensions to filter by (e.g., [".md", "py", "*.env*"])
            git_status: If True, include git status column
            git_detail: If True, include git status + last commit info

        Returns:
            List of HistoryEntry sorted by modified date descending
        """
        directory = Path(directory).expanduser().resolve()
        if not directory.exists():
            return []

        # Normalize filetype patterns
        normalized_filetypes = None
        if filetypes:
            normalized_filetypes = [self._normalize_extension(ft) for ft in filetypes]

        entries = []

        for root, dirs, files in os.walk(directory, followlinks=False):
            # Filter out skip directories in-place
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                file_path = Path(root) / filename

                # Check if should skip this file
                if self._should_skip_file(filename):
                    continue

                # Check filetype filter
                if normalized_filetypes and not self._matches_filetypes(filename, normalized_filetypes):
                    continue

                # Get file info
                try:
                    entry = self._create_entry(file_path, directory)
                    if entry:
                        entries.append(entry)
                except (OSError, PermissionError):
                    continue

        # Sort by modified date descending and return top N
        entries.sort(key=lambda e: e.modified_date, reverse=True)
        entries = entries[:count]

        # Add git info if requested
        if git_status or git_detail:
            self._add_git_info(entries, directory, include_commit=git_detail)

        return entries

    def _add_git_info(self, entries: list[HistoryEntry], base_dir: Path, include_commit: bool = False) -> None:
        """Add git information to entries.

        Args:
            entries: List of HistoryEntry to update in place
            base_dir: Base directory for git root detection
            include_commit: Whether to include commit details
        """
        from .git_utils import get_git_root, get_file_status, get_file_last_commit

        git_root = get_git_root(base_dir)

        for entry in entries:
            file_path = Path(entry.path)
            entry.git_status = get_file_status(file_path, git_root)

            if include_commit and git_root is not None:
                _, msg, relative = get_file_last_commit(file_path, git_root)
                entry.git_commit_relative = relative
                entry.git_commit_msg = msg

    def _normalize_extension(self, ext: str) -> str:
        """Normalize extension input to glob pattern.

        Args:
            ext: Extension like ".md", "md", "*.env*", "*local"

        Returns:
            Normalized pattern for fnmatch
        """
        # If already contains wildcard, use as-is
        if '*' in ext or '?' in ext:
            return ext.lower()

        # Add dot if missing
        if not ext.startswith('.'):
            ext = '.' + ext

        # Return as suffix match pattern
        return f"*{ext}".lower()

    def _should_skip_dir(self, dirname: str) -> bool:
        """Check if directory should be skipped.

        Args:
            dirname: Directory name (not full path)

        Returns:
            True if should skip
        """
        # Direct match
        if dirname in self.skip_dirs:
            return True

        # Pattern match (for things like *.egg-info)
        for pattern in self.skip_dirs:
            if '*' in pattern and fnmatch.fnmatch(dirname, pattern):
                return True

        return False

    def _should_skip_file(self, filename: str) -> bool:
        """Check if file should be skipped.

        Args:
            filename: Filename (not full path)

        Returns:
            True if should skip
        """
        filename_lower = filename.lower()

        # Check skip patterns
        for pattern in self.skip_patterns:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                return True

        # Dotfiles: skip unless in utility allowlist
        if filename.startswith('.'):
            return not self._is_utility_dotfile(filename)

        return False

    def _is_utility_dotfile(self, filename: str) -> bool:
        """Check if dotfile is a utility file we want to track.

        Args:
            filename: Filename starting with .

        Returns:
            True if this is a utility dotfile
        """
        filename_lower = filename.lower()

        for pattern in UTILITY_DOTFILE_PATTERNS:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                return True

        return False

    def _matches_filetypes(self, filename: str, patterns: list[str]) -> bool:
        """Check if filename matches any of the filetype patterns.

        Args:
            filename: Filename to check
            patterns: List of normalized patterns

        Returns:
            True if matches any pattern
        """
        filename_lower = filename.lower()

        for pattern in patterns:
            if fnmatch.fnmatch(filename_lower, pattern):
                return True

        return False

    def _create_entry(self, file_path: Path, base_dir: Path) -> Optional[HistoryEntry]:
        """Create a HistoryEntry for a file.

        Args:
            file_path: Absolute path to file
            base_dir: Base directory for relative path calculation

        Returns:
            HistoryEntry or None if file can't be read
        """
        try:
            stat = file_path.stat()

            # Read content for line and token counts
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                lines = len(content.splitlines())
                tokens = count_tokens(content)
            except (OSError, PermissionError, UnicodeDecodeError):
                # Can't read content, skip this file
                return None

            # Get extension
            ext = file_path.suffix if file_path.suffix else "(none)"

            # Calculate relative path
            try:
                relative = file_path.relative_to(base_dir)
            except ValueError:
                relative = file_path

            return HistoryEntry(
                path=str(file_path),
                relative_path=str(relative),
                modified_date=stat.st_mtime,
                extension=ext,
                lines=lines,
                tokens=tokens,
            )

        except (OSError, PermissionError):
            return None
