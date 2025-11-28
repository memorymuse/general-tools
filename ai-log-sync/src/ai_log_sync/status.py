"""Status display functionality."""
from __future__ import annotations

import click
from datetime import datetime

from .config import Config
from .index import Index
from .cloud import check_remote_status, is_rclone_installed


def show_status(config: Config) -> None:
    """Display current sync status and statistics."""
    click.echo("AI Log Sync Status")
    click.echo("=" * 40)

    # Config info
    click.echo()
    click.echo("Configuration:")
    click.echo(f"  Base directory:  {config.base_dir}")
    click.echo(f"  Inbox:           {config.inbox_dir}")
    click.echo(f"  Staging:         {config.staging_dir}")
    click.echo()

    # Cloud status
    click.echo("Cloud Storage:")
    if not config.cloud.enabled:
        click.echo("  Status: Disabled")
    else:
        status = check_remote_status(config.cloud)

        if not status["rclone_installed"]:
            click.echo(click.style("  rclone: NOT INSTALLED", fg="red"))
            click.echo("  Install with: brew install rclone")
        elif not status["remote_configured"]:
            click.echo(click.style(f"  Remote '{config.cloud.remote_name}': NOT CONFIGURED", fg="yellow"))
            click.echo("  Configure with: rclone config")
        elif not status["remote_accessible"]:
            click.echo(click.style("  Remote: NOT ACCESSIBLE", fg="red"))
            click.echo("  Check your internet connection or rclone config")
        else:
            click.echo(click.style("  Status: Connected", fg="green"))
            click.echo(f"  Remote: {config.cloud.remote_name}:{config.cloud.remote_path}")
            click.echo(f"  Files:  {status['file_count']}")
    click.echo()

    # Local index status
    click.echo("Local Index:")
    index_path = config.staging_dir / "index.json"

    if not index_path.exists():
        click.echo("  No local index (run 'ai-log-sync sync' first)")
    else:
        index = Index.load(index_path)
        stats = index.stats()

        click.echo(f"  Total conversations: {stats['total']}")
        click.echo()
        click.echo("  By source:")
        for source, count in sorted(stats["by_source"].items()):
            click.echo(f"    {source}: {count}")
    click.echo()

    # Inbox status
    click.echo("Inbox:")
    if not config.inbox_dir.exists():
        click.echo("  Inbox directory doesn't exist")
    else:
        zip_files = list(config.inbox_dir.glob("*.zip"))
        json_files = list(config.inbox_dir.glob("*.json"))

        if not zip_files and not json_files:
            click.echo("  Empty (no files to process)")
        else:
            if zip_files:
                click.echo(f"  ZIP files:  {len(zip_files)}")
                for zf in zip_files[:5]:  # Show first 5
                    click.echo(f"    - {zf.name}")
                if len(zip_files) > 5:
                    click.echo(f"    ... and {len(zip_files) - 5} more")

            if json_files:
                click.echo(f"  JSON files: {len(json_files)}")
    click.echo()

    # Source status
    click.echo("Sources:")
    for source_name, source_config in config.sources.items():
        status = "enabled" if source_config.enabled else "disabled"
        color = "green" if source_config.enabled else "yellow"
        click.echo(f"  {source_name}: {click.style(status, fg=color)}")
        if source_config.paths:
            for path in source_config.paths:
                click.echo(f"    Path: {path}")
