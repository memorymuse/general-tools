"""Configuration management for ai-log-sync."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import platform
import yaml


def get_default_config_path() -> Path:
    """Get the default config path based on OS."""
    return Path.home() / "ai-log-sync" / "config.yaml"


def get_default_base_dir() -> Path:
    """Get the default base directory for ai-log-sync data."""
    return Path.home() / "ai-log-sync"


@dataclass
class SourceConfig:
    """Configuration for a single source."""

    enabled: bool = True
    paths: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceConfig":
        return cls(
            enabled=data.get("enabled", True),
            paths=data.get("paths", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "paths": self.paths,
        }


@dataclass
class CloudConfig:
    """Configuration for cloud sync."""

    remote_name: str = "gdrive"
    remote_path: str = "ai-chat-logs"
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CloudConfig":
        return cls(
            remote_name=data.get("remote_name", "gdrive"),
            remote_path=data.get("remote_path", "ai-chat-logs"),
            enabled=data.get("enabled", True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote_name": self.remote_name,
            "remote_path": self.remote_path,
            "enabled": self.enabled,
        }


@dataclass
class Config:
    """Main configuration for ai-log-sync."""

    base_dir: Path
    inbox_dir: Path
    staging_dir: Path
    raw_dir: Path
    sources: dict[str, SourceConfig]
    cloud: CloudConfig

    @classmethod
    def default(cls) -> "Config":
        """Create a default configuration."""
        base_dir = get_default_base_dir()
        system = platform.system().lower()

        # Platform-specific default paths
        if system == "darwin":  # macOS
            claude_code_path = "~/.claude/projects"
            codex_path = "~/.codex"
        elif system == "windows":
            claude_code_path = "~/.claude/projects"
            codex_path = "~/.codex"
        else:  # Linux/WSL
            claude_code_path = "~/.claude/projects"
            codex_path = "~/.codex"

        return cls(
            base_dir=base_dir,
            inbox_dir=base_dir / "inbox",
            staging_dir=base_dir / "staging",
            raw_dir=base_dir / "staging" / "raw",
            sources={
                "claude-code": SourceConfig(
                    enabled=True,
                    paths=[claude_code_path],
                ),
                "codex": SourceConfig(
                    enabled=True,
                    paths=[codex_path],
                ),
                "chatgpt-export": SourceConfig(
                    enabled=True,
                    paths=[],  # Uses inbox directory
                ),
                "claude-web-export": SourceConfig(
                    enabled=True,
                    paths=[],  # Uses inbox directory
                ),
                "gemini": SourceConfig(
                    enabled=True,
                    paths=[],  # Uses inbox directory
                ),
                "grok": SourceConfig(
                    enabled=True,
                    paths=[],  # Uses inbox directory
                ),
            },
            cloud=CloudConfig(),
        )

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        base_dir = Path(data.get("base_dir", get_default_base_dir())).expanduser()

        return cls(
            base_dir=base_dir,
            inbox_dir=Path(data.get("inbox_dir", base_dir / "inbox")).expanduser(),
            staging_dir=Path(data.get("staging_dir", base_dir / "staging")).expanduser(),
            raw_dir=Path(data.get("raw_dir", base_dir / "staging" / "raw")).expanduser(),
            sources={
                name: SourceConfig.from_dict(src_data)
                for name, src_data in data.get("sources", {}).items()
            },
            cloud=CloudConfig.from_dict(data.get("cloud", {})),
        )

    def save(self, path: Path) -> None:
        """Save configuration to a YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "base_dir": str(self.base_dir),
            "inbox_dir": str(self.inbox_dir),
            "staging_dir": str(self.staging_dir),
            "raw_dir": str(self.raw_dir),
            "sources": {name: src.to_dict() for name, src in self.sources.items()},
            "cloud": self.cloud.to_dict(),
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
