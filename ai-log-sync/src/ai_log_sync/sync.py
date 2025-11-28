"""Main sync orchestration logic."""
from __future__ import annotations

from pathlib import Path
import json
import click

from .config import Config
from .index import Index, MergeResult
from .models import Conversation
from .cloud import pull_index, push_staging
from .collectors import (
    ClaudeCodeCollector,
    ChatGPTExportCollector,
    ClaudeWebExportCollector,
)


def run_sync(config: Config, dry_run: bool = False, push: bool = True) -> None:
    """
    Run the full sync process.

    1. Pull remote index
    2. Collect from all local sources
    3. Merge into local index
    4. Save conversation files
    5. Push to cloud (unless --no-push)
    """
    click.echo("AI Log Sync")
    click.echo("=" * 40)

    if dry_run:
        click.echo(click.style("[DRY RUN] No changes will be made", fg="yellow"))
        click.echo()

    # Ensure directories exist
    config.staging_dir.mkdir(parents=True, exist_ok=True)
    (config.staging_dir / "logs").mkdir(exist_ok=True)

    # Step 1: Pull remote index
    click.echo("Pulling remote index...")
    index_path = config.staging_dir / "index.json"

    if push and config.cloud.enabled:
        result = pull_index(config.cloud, index_path)
        if result.success:
            click.echo(f"  {result.message}")
        else:
            click.echo(click.style(f"  Warning: {result.message}", fg="yellow"))
    else:
        click.echo("  Skipped (cloud sync disabled)")

    # Load existing index
    index = Index.load(index_path)
    click.echo(f"  Loaded {len(index)} existing conversations")
    click.echo()

    # Step 2: Collect from all sources
    collectors = _get_collectors(config, dry_run=dry_run)

    stats = {
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    for collector in collectors:
        if not collector.is_enabled():
            continue

        source_name = collector.source_name
        click.echo(f"Collecting from {source_name}...")

        source_stats = {"collected": 0, "added": 0, "updated": 0, "skipped": 0}

        try:
            for conv in collector.collect():
                source_stats["collected"] += 1

                # Save conversation file
                raw_path = f"logs/{conv.source}/{conv.native_id}.json"
                full_path = config.staging_dir / raw_path

                if not dry_run:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, "w") as f:
                        json.dump(conv.to_dict(), f, indent=2, default=str)

                # Merge into index
                result = index.merge(conv, raw_path)

                if result.action == "added":
                    click.echo()  # Break dot line
                    click.echo(f"  [+] {conv.title[:60]}")
                    source_stats["added"] += 1
                    stats["added"] += 1
                elif result.action == "updated":
                    click.echo()  # Break dot line
                    click.echo(f"  [U] {conv.title[:60]} ({result.reason})")
                    source_stats["updated"] += 1
                    stats["updated"] += 1
                else:
                    click.echo(".", nl=False)
                    source_stats["skipped"] += 1
                    stats["skipped"] += 1
                    
                # Flush stdout to ensure dots appear immediately
                import sys
                sys.stdout.flush()

        except Exception as e:
            click.echo()  # Break dot line
            click.echo(click.style(f"  Error: {e}", fg="red"))
            stats["errors"] += 1
            continue

        click.echo()  # Newline after source is done

    click.echo()

    # Step 3: Save index
    click.echo("Saving index...")
    if not dry_run:
        index.save(index_path)
    click.echo(f"  Total: {len(index)} conversations")
    click.echo()

    # Step 4: Push to cloud
    if push and config.cloud.enabled:
        click.echo("Pushing to cloud storage...")
        result = push_staging(config.cloud, config.staging_dir, dry_run=dry_run)
        if result.success:
            click.echo(click.style(f"  {result.message}", fg="green"))
        else:
            click.echo(click.style(f"  Error: {result.message}", fg="red"))
    else:
        click.echo("Cloud push skipped")

    click.echo()

    # Summary
    click.echo("=" * 40)
    click.echo("Summary:")
    click.echo(f"  New conversations:     {stats['added']}")
    click.echo(f"  Updated conversations: {stats['updated']}")
    click.echo(f"  Unchanged (skipped):   {stats['skipped']}")
    if stats["errors"]:
        click.echo(click.style(f"  Errors:                {stats['errors']}", fg="red"))

    if dry_run:
        click.echo()
        click.echo(click.style("[DRY RUN] No changes were made", fg="yellow"))


def _get_collectors(config: Config, dry_run: bool = False) -> list:
    """Create collector instances from config."""
    collectors = []

    # Claude Code
    if "claude-code" in config.sources:
        collectors.append(
            ClaudeCodeCollector(
                config.sources["claude-code"],
                inbox_dir=config.inbox_dir,
                raw_dir=config.raw_dir,
                dry_run=dry_run,
            )
        )

    # ChatGPT export
    if "chatgpt-export" in config.sources:
        collectors.append(
            ChatGPTExportCollector(
                config.sources["chatgpt-export"],
                inbox_dir=config.inbox_dir,
                raw_dir=config.raw_dir,
                dry_run=dry_run,
            )
        )

    # Claude.ai export
    if "claude-web-export" in config.sources:
        collectors.append(
            ClaudeWebExportCollector(
                config.sources["claude-web-export"],
                inbox_dir=config.inbox_dir,
                raw_dir=config.raw_dir,
                dry_run=dry_run,
            )
        )

    return collectors
