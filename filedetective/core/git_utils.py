"""Git utilities for file status and history."""
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class GitFileInfo:
    """Git information for a file."""
    status: str              # M, A, ?, ✓, !, or - (not in repo)
    last_commit_date: Optional[datetime] = None
    last_commit_msg: Optional[str] = None
    last_commit_relative: Optional[str] = None  # "2d ago", "5h ago"


def get_git_root(path: Path) -> Optional[Path]:
    """Get the git repository root for a path.

    Args:
        path: File or directory path

    Returns:
        Git root path or None if not in a repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path if path.is_dir() else path.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def get_file_status(file_path: Path, git_root: Optional[Path] = None) -> str:
    """Get git status for a single file.

    Args:
        file_path: Path to file
        git_root: Optional git root (will be detected if not provided)

    Returns:
        Status character: M (modified), A (staged), ? (untracked), ✓ (clean), ! (ignored), - (not in repo)
    """
    if git_root is None:
        git_root = get_git_root(file_path)

    if git_root is None:
        return "-"

    try:
        # Get path relative to git root
        try:
            rel_path = file_path.resolve().relative_to(git_root)
        except ValueError:
            return "-"  # File not under git root

        # Run git status --porcelain for this file
        result = subprocess.run(
            ["git", "status", "--porcelain", "--ignored", str(rel_path)],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return "-"

        output = result.stdout.strip()

        if not output:
            # No output means file is tracked and clean
            # But verify it's actually tracked
            check = subprocess.run(
                ["git", "ls-files", str(rel_path)],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if check.stdout.strip():
                return "✓"  # Tracked and clean
            else:
                return "?"  # Not tracked (shouldn't happen if status was empty)

        # Parse porcelain output (XY format)
        # X = index status, Y = worktree status
        status_code = output[:2]

        if status_code == "!!":
            return "!"  # Ignored
        elif status_code == "??":
            return "?"  # Untracked
        elif status_code[0] in "MADRC":
            return "A"  # Staged (Added/Modified/Deleted/Renamed/Copied in index)
        elif status_code[1] in "MD":
            return "M"  # Modified in worktree
        else:
            return "✓"  # Default to clean

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "-"


def get_file_last_commit(file_path: Path, git_root: Optional[Path] = None) -> tuple[Optional[datetime], Optional[str], Optional[str]]:
    """Get last commit info for a file.

    Args:
        file_path: Path to file
        git_root: Optional git root

    Returns:
        Tuple of (commit_date, commit_message, relative_time) or (None, None, None)
    """
    if git_root is None:
        git_root = get_git_root(file_path)

    if git_root is None:
        return None, None, None

    try:
        rel_path = file_path.resolve().relative_to(git_root)
    except ValueError:
        return None, None, None

    try:
        # Get last commit date and message
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct|%s|%cr", "--", str(rel_path)],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None, None, None

        parts = result.stdout.strip().split("|", 2)
        if len(parts) >= 3:
            timestamp = int(parts[0])
            message = parts[1][:40]  # Truncate message
            relative = parts[2]

            # Shorten relative time
            relative = (relative
                .replace(" ago", "")
                .replace(" minutes", "m")
                .replace(" minute", "m")
                .replace(" hours", "h")
                .replace(" hour", "h")
                .replace(" days", "d")
                .replace(" day", "d")
                .replace(" weeks", "w")
                .replace(" week", "w")
                .replace(" months", "mo")
                .replace(" month", "mo")
                .replace(" years", "y")
                .replace(" year", "y")
            )

            return datetime.fromtimestamp(timestamp), message, relative

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        pass

    return None, None, None


def get_git_info(file_path: Path, include_commit: bool = False) -> GitFileInfo:
    """Get complete git info for a file.

    Args:
        file_path: Path to file
        include_commit: Whether to include last commit details

    Returns:
        GitFileInfo dataclass
    """
    file_path = Path(file_path).resolve()
    git_root = get_git_root(file_path)

    status = get_file_status(file_path, git_root)

    if include_commit and git_root is not None:
        commit_date, commit_msg, commit_relative = get_file_last_commit(file_path, git_root)
        return GitFileInfo(
            status=status,
            last_commit_date=commit_date,
            last_commit_msg=commit_msg,
            last_commit_relative=commit_relative
        )

    return GitFileInfo(status=status)


def get_bulk_git_status(file_paths: list[Path], base_dir: Path) -> dict[str, str]:
    """Get git status for multiple files efficiently.

    Args:
        file_paths: List of file paths
        base_dir: Base directory (used to find git root)

    Returns:
        Dict mapping file path strings to status characters
    """
    git_root = get_git_root(base_dir)
    if git_root is None:
        return {str(p): "-" for p in file_paths}

    try:
        # Get all statuses at once
        result = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"],
            cwd=git_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {str(p): "-" for p in file_paths}

        # Parse into a dict
        status_map = {}
        for line in result.stdout.splitlines():
            if len(line) >= 3:
                status_code = line[:2]
                file_name = line[3:]

                if status_code == "!!":
                    status_map[file_name] = "!"
                elif status_code == "??":
                    status_map[file_name] = "?"
                elif status_code[0] in "MADRC":
                    status_map[file_name] = "A"
                elif status_code[1] in "MD":
                    status_map[file_name] = "M"

        # Map our files to statuses
        result_map = {}
        for file_path in file_paths:
            try:
                rel_path = str(file_path.resolve().relative_to(git_root))
                result_map[str(file_path)] = status_map.get(rel_path, "✓")
            except ValueError:
                result_map[str(file_path)] = "-"

        return result_map

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {str(p): "-" for p in file_paths}
