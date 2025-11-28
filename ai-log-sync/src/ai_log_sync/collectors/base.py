"""Base collector class for all source collectors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Any
import json

from ..config import SourceConfig
from ..models import Conversation


class BaseCollector(ABC):
    """Abstract base class for all source collectors."""

    source_name: str  # Must be set by subclass

    def __init__(
        self,
        config: SourceConfig,
        inbox_dir: Path | None = None,
        raw_dir: Path | None = None,
        dry_run: bool = False,
    ):
        self.config = config
        self.inbox_dir = inbox_dir
        self.raw_dir = raw_dir
        self.dry_run = dry_run

    @abstractmethod
    def collect(self) -> Iterator[Conversation]:
        """
        Collect conversations from this source.

        Yields:
            Conversation objects normalized to the common schema.
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this collector is enabled."""
        return self.config.enabled

    def _expand_paths(self) -> list[Path]:
        """Expand configured paths, handling ~ and globs."""
        paths = []
        for path_str in self.config.paths:
            path = Path(path_str).expanduser()
            if path.exists():
                paths.append(path)
        return paths

    def _archive_raw(self, data: Any, native_id: str, extension: str, is_binary: bool = False) -> Path:
        """
        Archive raw source data to the staging directory.
        Returns the path to the archived file.
        """
        # Create source-specific raw directory
        raw_source_dir = self.raw_dir / self.source_name
        
        # Handle subdirectories in native_id (e.g. attachments/foo.jpg)
        if "/" in native_id:
            raw_source_dir = raw_source_dir / Path(native_id).parent
            native_id = Path(native_id).name
            
        if not self.dry_run:
            raw_source_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{native_id}.{extension}" if extension else native_id
        target_path = raw_source_dir / filename

        # Prepare content
        if is_binary:
            content = data
        else:
            if isinstance(data, str):
                content = data
            else:
                content = json.dumps(data, indent=2, default=str)

        # Deduplication check
        if target_path.exists() and not self.dry_run:
            try:
                if is_binary:
                    with open(target_path, "rb") as f:
                        existing_content = f.read()
                else:
                    with open(target_path, "r") as f:
                        existing_content = f.read()
                
                if content == existing_content:
                    return target_path
            except Exception:
                pass

        if not self.dry_run:
            mode = "wb" if is_binary else "w"
            with open(target_path, mode) as f:
                f.write(content)

        return target_path
