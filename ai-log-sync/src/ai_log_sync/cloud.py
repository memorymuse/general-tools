"""Cloud sync functionality using rclone."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import shutil

from .config import CloudConfig


@dataclass
class SyncResult:
    """Result of a cloud sync operation."""

    success: bool
    message: str
    files_transferred: int = 0
    bytes_transferred: int = 0


def is_rclone_installed() -> bool:
    """Check if rclone is installed and available."""
    return shutil.which("rclone") is not None


def is_remote_configured(remote_name: str) -> bool:
    """Check if a specific rclone remote is configured."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False
        remotes = result.stdout.strip().split("\n")
        return f"{remote_name}:" in remotes
    except Exception:
        return False


def pull_index(cloud_config: CloudConfig, local_path: Path) -> SyncResult:
    """
    Pull the index.json from cloud storage.

    Args:
        cloud_config: Cloud configuration
        local_path: Local path to save index.json

    Returns:
        SyncResult indicating success or failure
    """
    if not is_rclone_installed():
        return SyncResult(
            success=False,
            message="rclone is not installed. Install with: brew install rclone",
        )

    if not is_remote_configured(cloud_config.remote_name):
        return SyncResult(
            success=False,
            message=f"rclone remote '{cloud_config.remote_name}' not configured. Run: rclone config",
        )

    remote_path = f"{cloud_config.remote_name}:{cloud_config.remote_path}/index.json"
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["rclone", "copy", remote_path, str(local_path.parent), "--checksum"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            # File might not exist yet (first sync) - that's okay
            if "not found" in result.stderr.lower() or "404" in result.stderr:
                return SyncResult(
                    success=True,
                    message="No remote index found (first sync)",
                )
            return SyncResult(
                success=False,
                message=f"rclone error: {result.stderr}",
            )

        return SyncResult(
            success=True,
            message="Index pulled successfully",
        )

    except subprocess.TimeoutExpired:
        return SyncResult(
            success=False,
            message="rclone timed out",
        )
    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Error: {e}",
        )


def push_staging(cloud_config: CloudConfig, staging_dir: Path, dry_run: bool = False) -> SyncResult:
    """
    Push staging directory to cloud storage.

    Args:
        cloud_config: Cloud configuration
        staging_dir: Local staging directory to push
        dry_run: If True, show what would be done without making changes

    Returns:
        SyncResult indicating success or failure
    """
    if not is_rclone_installed():
        return SyncResult(
            success=False,
            message="rclone is not installed. Install with: brew install rclone",
        )

    if not is_remote_configured(cloud_config.remote_name):
        return SyncResult(
            success=False,
            message=f"rclone remote '{cloud_config.remote_name}' not configured. Run: rclone config",
        )

    if not staging_dir.exists():
        return SyncResult(
            success=False,
            message=f"Staging directory does not exist: {staging_dir}",
        )

    remote_path = f"{cloud_config.remote_name}:{cloud_config.remote_path}"

    cmd = [
        "rclone",
        "sync",
        str(staging_dir),
        remote_path,
        "--checksum",
        "-v",  # Verbose for transfer stats
    ]

    if dry_run:
        cmd.append("--dry-run")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        transferred = 0
        
        # Read output line by line
        while True:
            if process.stdout:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    line = line.strip()
                    # Print interesting lines to show progress
                    if "Transferred:" in line or "Copied" in line or "Deleted" in line:
                         print(f"  {line}")
                    
                    # Parse stats
                    if "Transferred:" in line:
                        parts = line.split()
                        for part in parts:
                            if part.isdigit():
                                transferred = int(part)
                                break

        if process.returncode != 0:
            return SyncResult(
                success=False,
                message="rclone failed (check output above)",
            )

        action = "Would transfer" if dry_run else "Transferred"
        return SyncResult(
            success=True,
            message=f"{action} files to {remote_path}",
            files_transferred=transferred,
        )

    except Exception as e:
        return SyncResult(
            success=False,
            message=f"Error: {e}",
        )


def check_remote_status(cloud_config: CloudConfig) -> dict:
    """
    Check the status of the remote storage.

    Returns:
        Dict with status information
    """
    status = {
        "rclone_installed": is_rclone_installed(),
        "remote_configured": False,
        "remote_accessible": False,
        "file_count": 0,
    }

    if not status["rclone_installed"]:
        return status

    status["remote_configured"] = is_remote_configured(cloud_config.remote_name)

    if not status["remote_configured"]:
        return status

    # Try to list remote to check accessibility
    remote_path = f"{cloud_config.remote_name}:{cloud_config.remote_path}"
    try:
        result = subprocess.run(
            ["rclone", "lsf", remote_path, "--recursive"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            status["remote_accessible"] = True
            files = [f for f in result.stdout.strip().split("\n") if f]
            status["file_count"] = len(files)

    except Exception:
        pass

    return status
