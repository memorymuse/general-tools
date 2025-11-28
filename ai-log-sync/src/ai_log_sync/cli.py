"""CLI entry point for ai-log-sync."""
from __future__ import annotations

import click
from pathlib import Path

from .config import Config, get_default_config_path
from .sync import run_sync
from .status import show_status


@click.group()
@click.version_option()
def main():
    """AI Log Sync - Aggregate AI conversation logs from multiple platforms."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False, path_type=Path),
    help="Path to config file",
)
def init(config: Path | None):
    """Initialize ai-log-sync configuration and directories."""
    config_path = config or get_default_config_path()

    if config_path.exists():
        click.echo(f"Config already exists at {config_path}")
        if not click.confirm("Overwrite?"):
            return

    # Create directories
    base_dir = config_path.parent
    (base_dir / "inbox").mkdir(parents=True, exist_ok=True)
    (base_dir / "staging" / "logs").mkdir(parents=True, exist_ok=True)

    # Write default config
    default_config = Config.default()
    default_config.save(config_path)

    click.echo(f"Created config at {config_path}")
    click.echo(f"Created inbox at {base_dir / 'inbox'}")
    click.echo(f"Created staging at {base_dir / 'staging'}")
    click.echo("\nNext steps:")
    click.echo("  1. Install rclone: brew install rclone (or apt install rclone)")
    click.echo("  2. Configure rclone: rclone config")
    click.echo("  3. Run sync: ai-log-sync sync")


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config file",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--no-push", is_flag=True, help="Collect and merge locally, but don't push to cloud")
def sync(config: Path | None, dry_run: bool, no_push: bool):
    """Collect logs from all sources and sync to cloud storage."""
    config_path = config or get_default_config_path()

    if not config_path.exists():
        click.echo(f"Config not found at {config_path}")
        click.echo("Run 'ai-log-sync init' first")
        raise SystemExit(1)

    cfg = Config.load(config_path)
    run_sync(cfg, dry_run=dry_run, push=not no_push)


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config file",
)
def status(config: Path | None):
    """Show current sync status and statistics."""
    config_path = config or get_default_config_path()

    if not config_path.exists():
        click.echo(f"Config not found at {config_path}")
        click.echo("Run 'ai-log-sync init' first")
        raise SystemExit(1)

    cfg = Config.load(config_path)
    show_status(cfg)


if __name__ == "__main__":
    main()
