"""File discovery with priority-based search."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import fnmatch
import yaml


@dataclass
class FileMatch:
    """Represents a matched file with metadata."""
    path: str
    priority: int
    modified_date: float
    size: int

    @property
    def display_path(self) -> str:
        """Get display-friendly path with ~ for home directory."""
        return str(Path(self.path).expanduser()).replace(str(Path.home()), "~")


class FileFinder:
    """Handles file discovery across priority directories."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize file finder.

        Args:
            config_path: Path to config.yaml (default: same directory as this file)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Expand paths and sort by priority
        self.search_dirs = sorted(
            self.config["search_directories"],
            key=lambda x: x["priority"]
        )

        self.skip_dirs = set(self.config["skip_directories"])
        self.skip_patterns = self.config["skip_patterns"]

    def find_files(
        self,
        pattern: str,
        content_search: Optional[str] = None,
        local_dir: Optional[Path] = None
    ) -> list[FileMatch]:
        """Find files matching pattern across priority directories.

        Supports three matching modes:
        1. Filename-only (no '/' in pattern): Matches against filename only
           Example: "storage.py", "*.md", "*project*"

        2. Path-based (contains '/'): Matches against relative path from each search root
           Example: "cc-*/drafts/*.md", "*/memos/design/*.md"

        3. Explicit directory prefix: If pattern starts with an existing directory path
           (like ~/cc-projects/*pattern*), searches that directory directly
           Example: "~/cc-projects/*SELF-REVIEW*" searches ~/cc-projects/

        Args:
            pattern: Filename or path pattern to search for.
                    Use wildcards (*) for flexible matching.
                    Include '/' for path-based matching.
            content_search: Optional text to search for in file contents
            local_dir: If provided, search only this directory instead of configured dirs

        Returns:
            List of FileMatch objects, sorted by priority then date
        """
        matches = []

        # If local_dir specified, search only that directory
        if local_dir is not None:
            local_path = Path(local_dir).expanduser().resolve()
            if local_path.exists():
                dir_matches = self._search_directory(
                    local_path,
                    pattern,
                    priority=0,  # Local gets highest priority
                    recursive=True,
                    exclude=set(),
                    content_search=content_search
                )
                matches.extend(dir_matches)
            # Sort by date only (all same priority)
            matches.sort(key=lambda m: -m.modified_date)
            return matches

        # Check if pattern contains an explicit directory prefix
        # e.g., "~/cc-projects/*SELF-REVIEW*" -> search ~/cc-projects/ with pattern "*SELF-REVIEW*"
        explicit_dir, filename_pattern = self._extract_explicit_directory(pattern)
        if explicit_dir is not None:
            dir_matches = self._search_directory(
                explicit_dir,
                filename_pattern,
                priority=0,  # Explicit paths get highest priority
                recursive=True,
                exclude=set(),
                content_search=content_search
            )
            matches.extend(dir_matches)
            # Sort by date only (all same priority)
            matches.sort(key=lambda m: -m.modified_date)
            return matches

        for search_dir in self.search_dirs:
            dir_path = Path(search_dir["path"]).expanduser()
            priority = search_dir["priority"]
            recursive = search_dir.get("recursive", True)
            exclude = set(search_dir.get("exclude", []))

            if not dir_path.exists():
                continue

            # Search directory
            dir_matches = self._search_directory(
                dir_path,
                pattern,
                priority,
                recursive,
                exclude,
                content_search
            )
            matches.extend(dir_matches)

        # Sort by priority (ascending), then by modified date (descending)
        matches.sort(key=lambda m: (m.priority, -m.modified_date))

        return matches

    def _search_directory(
        self,
        dir_path: Path,
        pattern: str,
        priority: int,
        recursive: bool,
        exclude: set[str],
        content_search: Optional[str] = None
    ) -> list[FileMatch]:
        """Search a single directory for matches.

        Args:
            dir_path: Directory to search
            pattern: Filename or glob pattern
            priority: Priority level
            recursive: Whether to search subdirectories
            exclude: Set of subdirectories to exclude
            content_search: Optional content to search for

        Returns:
            List of FileMatch objects
        """
        matches = []

        try:
            if recursive:
                # Walk directory tree
                for root, dirs, files in os.walk(dir_path, followlinks=False):
                    # Filter out skip directories and excluded subdirs
                    dirs[:] = [
                        d for d in dirs
                        if d not in self.skip_dirs and d not in exclude
                    ]

                    # Check each file
                    for filename in files:
                        file_path = Path(root) / filename

                        # Skip patterns
                        if self._should_skip(file_path):
                            continue

                        # Match pattern (with path support)
                        if self._matches_pattern(
                            filename,
                            pattern,
                            full_path=str(file_path),
                            base_path=str(dir_path)
                        ):
                            # If content search specified, check content
                            if content_search is not None:
                                if not self._content_matches(file_path, content_search):
                                    continue

                            # Add match
                            try:
                                stat = file_path.stat()
                                matches.append(FileMatch(
                                    path=str(file_path),
                                    priority=priority,
                                    modified_date=stat.st_mtime,
                                    size=stat.st_size
                                ))
                            except (OSError, PermissionError):
                                # Skip files we can't access
                                continue
            else:
                # Non-recursive search
                for item in dir_path.iterdir():
                    if item.is_file():
                        if self._should_skip(item):
                            continue

                        if self._matches_pattern(
                            item.name,
                            pattern,
                            full_path=str(item),
                            base_path=str(dir_path)
                        ):
                            if content_search is not None:
                                if not self._content_matches(item, content_search):
                                    continue

                            try:
                                stat = item.stat()
                                matches.append(FileMatch(
                                    path=str(item),
                                    priority=priority,
                                    modified_date=stat.st_mtime,
                                    size=stat.st_size
                                ))
                            except (OSError, PermissionError):
                                continue

        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

        return matches

    def _extract_explicit_directory(self, pattern: str) -> tuple[Optional[Path], str]:
        """Extract explicit directory prefix from pattern if present.

        Handles patterns like:
        - "~/cc-projects/*SELF-REVIEW*" -> (Path(~/cc-projects), "*SELF-REVIEW*")
        - "/Users/foo/bar/*test*" -> (Path(/Users/foo/bar), "*test*")
        - "cc-*/drafts/*.md" -> (None, "cc-*/drafts/*.md")  # No explicit dir, relative pattern

        The key insight: if the pattern starts with a path that resolves to
        a real directory (after expanding ~), we extract it and use the
        remaining pattern as the filename pattern.

        Args:
            pattern: The pattern to analyze

        Returns:
            Tuple of (directory_path, filename_pattern) if explicit dir found,
            or (None, pattern) if no explicit directory
        """
        # Expand ~ in pattern
        expanded = Path(pattern).expanduser()
        pattern_str = str(expanded)

        # Only consider patterns that look like absolute paths or start with ~
        if not pattern.startswith('~') and not pattern.startswith('/'):
            return None, pattern

        # Walk the path from root to find the longest existing directory prefix
        # e.g., ~/cc-projects/*SELF-REVIEW* -> find ~/cc-projects/ exists
        parts = Path(pattern_str).parts
        for i in range(len(parts), 0, -1):
            candidate = Path(*parts[:i])
            if candidate.exists() and candidate.is_dir():
                # Found an existing directory prefix
                remaining_parts = parts[i:]
                if remaining_parts:
                    # There's a filename pattern after the directory
                    filename_pattern = str(Path(*remaining_parts))
                    return candidate, filename_pattern
                else:
                    # The pattern IS a directory - search all files in it
                    return candidate, "*"

        return None, pattern

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped.

        Args:
            path: File path to check

        Returns:
            True if file should be skipped
        """
        # Check skip patterns
        for pattern in self.skip_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def _matches_pattern(self, filename: str, pattern: str, full_path: str = None, base_path: str = None) -> bool:
        """Check if filename or path matches pattern (case-insensitive).

        Implements two matching modes:
        1. Filename-only (no '/' in pattern): Matches filename using fnmatch
        2. Path-based (contains '/'): Matches relative path from base_path

        For path-based matching, automatically tries multiple depth prefixes
        to handle deeply nested files (pattern, */pattern, */*/pattern).

        All matching is case-insensitive for user convenience.

        Args:
            filename: Name of file
            pattern: Pattern to match (glob-style with * and ?)
            full_path: Full file path (required for path-based matching)
            base_path: Base directory path (to compute relative path)

        Returns:
            True if matches, False otherwise

        Examples:
            _matches_pattern("Test.PY", "*.py") -> True (case-insensitive)
            _matches_pattern("CLAUDE.md", "claude.md") -> True
            _matches_pattern("test.md", "CC-*/DRAFTS/*.MD", "/path/to/cc-opts/drafts/test.md", "/path/to") -> True
        """
        # If pattern contains path separators, do path-based matching
        if '/' in pattern or '\\' in pattern:
            if full_path and base_path:
                # Get relative path from base
                try:
                    rel_path = Path(full_path).relative_to(base_path)
                    rel_path_str = str(rel_path)

                    # Case-insensitive matching
                    rel_path_lower = rel_path_str.lower()
                    pattern_lower = pattern.lower()

                    # Try fnmatch on relative path
                    if fnmatch.fnmatch(rel_path_lower, pattern_lower):
                        return True

                    # Also try with wildcard prefix (allows **/pattern)
                    if fnmatch.fnmatch(rel_path_lower, f"*/{pattern_lower}"):
                        return True
                    if fnmatch.fnmatch(rel_path_lower, f"*/*/{pattern_lower}"):
                        return True

                except ValueError:
                    # Path not relative to base, skip
                    pass
            return False

        # No path separator - match on filename only
        # Case-insensitive matching for all comparisons
        filename_lower = filename.lower()
        pattern_lower = pattern.lower()

        # Try exact match
        if filename_lower == pattern_lower:
            return True

        # Try glob pattern
        if fnmatch.fnmatch(filename_lower, pattern_lower):
            return True

        return False

    def _content_matches(self, file_path: Path, search_term: str) -> bool:
        """Check if file content contains search term.

        Args:
            file_path: Path to file
            search_term: Text to search for

        Returns:
            True if content contains search term
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return search_term in content
        except (OSError, PermissionError, UnicodeDecodeError):
            return False
