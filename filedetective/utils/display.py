"""Display formatting using Rich library."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from zoneinfo import ZoneInfo

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from analyzers.base_analyzer import FileStats, AggregateStats
from utils.file_utils import format_date
from core.tokenizer import format_size


console = Console()


def display_single_file(stats: FileStats) -> None:
    """Display statistics for a single file.

    Args:
        stats: FileStats object
    """
    # Header
    console.print(f"\n[bold cyan]File:[/] {stats.display_name} ([dim]{stats.display_path}[/])")
    console.print(f"[dim]Modified:[/] {format_date(stats.modified_date)}")
    console.print(f"[dim]Type:[/] {stats.file_type}")
    console.print()

    # Core stats
    _display_core_stats(stats)

    # Structure (if present)
    if stats.structure:
        console.print(f"\n[bold green]Structure:[/]")
        console.print(Panel(stats.structure, border_style="green", padding=(1, 2)))

    # Dependencies (if present)
    if stats.dependencies:
        console.print(f"\n[bold yellow]Dependencies:[/]")
        console.print(Panel(stats.dependencies, border_style="yellow", padding=(1, 2)))

    console.print()  # Final newline


def display_multiple_files(agg_stats: AggregateStats) -> None:
    """Display statistics for multiple files.

    Args:
        agg_stats: AggregateStats object with individual stats
    """
    # Sort by token count descending
    sorted_stats = sorted(
        agg_stats.individual_stats,
        key=lambda s: s.tokens,
        reverse=True
    )

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("File", style="cyan", no_wrap=True, width=30)
    table.add_column("Tokens", justify="right", style="magenta")
    table.add_column("Lines", justify="right", style="blue")
    table.add_column("Chars", justify="right", style="green")

    # Add word column if text files
    has_words = any(s.words is not None for s in sorted_stats)
    if has_words:
        table.add_column("Words", justify="right", style="yellow")

    # Add rows
    for i, stats in enumerate(sorted_stats):
        marker = ""
        if i == 0:
            marker = " [dim]\\[largest][/]"
        elif i == len(sorted_stats) - 1:
            marker = " [dim]\\[smallest][/]"

        row = [
            stats.display_name + marker,
            f"{stats.tokens:,}",
            f"{stats.lines:,}",
            f"{stats.chars:,}",
        ]

        if has_words:
            row.append(f"{stats.words:,}" if stats.words else "-")

        table.add_row(*row)

    console.print(f"\n[bold]Analyzed {agg_stats.file_count} files:[/]\n")
    console.print(table)

    # Aggregate totals
    console.print(f"\n[bold cyan]Totals ({agg_stats.file_count} files):[/]")
    console.print(f"  tokens:  [magenta]{agg_stats.total_tokens:>7,}[/]  │  "
                  f"lines:  [blue]{agg_stats.total_lines:>7,}[/]  │  "
                  f"chars:  [green]{agg_stats.total_chars:>7,}[/]", end="")

    if agg_stats.total_words is not None:
        console.print(f"  │  words:  [yellow]{agg_stats.total_words:>7,}[/]")
    else:
        console.print()

    console.print()


def display_search_results(matches: List, query: Union[str, List[str]]) -> None:
    """Display file search results.

    Args:
        matches: List of FileMatch objects
        query: Original search query (single pattern or list of patterns)
    """
    # Format query display
    if isinstance(query, list):
        if len(query) == 1:
            query_display = f'"{query[0]}"'
        else:
            query_display = f'{len(query)} patterns'
    else:
        query_display = f'"{query}"'

    if not matches:
        console.print(f"\n[red]No matches found for[/] [yellow]{query_display}[/]\n")
        console.print("[dim]Searched directories:[/]")
        console.print("  1. ~/projects/muse-v1/*")
        console.print("  2. ~/projects/* (excluding muse-v1, muse-v0)")
        console.print("  3. ~/.claude/*")
        console.print("  4. ~/projects/muse-v0/*\n")
        return

    console.print(f"\n[bold]Found {len(matches)} matches for[/] [yellow]{query_display}[/]:\n")

    for i, match in enumerate(matches, 1):
        console.print(f"[cyan]\\[{i}][/] {match.display_path}")
        console.print(f"    [dim]Modified:[/] {format_date(match.modified_date)}")
        console.print(f"    [dim]Size:[/] {format_size(match.size)}\n")


def display_error(message: str) -> None:
    """Display error message.

    Args:
        message: Error message
    """
    console.print(f"\n[bold red]Error:[/] {message}\n")


def _display_core_stats(stats: FileStats) -> None:
    """Display core statistics line.

    Args:
        stats: FileStats object
    """
    # Build stats line
    parts = [
        f"tokens:  [magenta]{stats.tokens:>7,}[/]",
        f"lines:  [blue]{stats.lines:>7,}[/]",
    ]

    if stats.words is not None:
        parts.append(f"words:  [yellow]{stats.words:>7,}[/]")

    parts.append(f"chars:  [green]{stats.chars:>7,}[/]")

    console.print("  │  ".join(parts))

    # Build rate line
    rate_parts = []
    if stats.tokens_per_line_mean is not None:
        rate_parts.append(
            f"tks/ln:  [magenta]{stats.tokens_per_line_mean:>5.1f}[/]  "
            f"[dim](med: {stats.tokens_per_line_median})[/]"
        )

    if stats.words_per_line_mean is not None:
        rate_parts.append(
            f"words/ln:  [yellow]{stats.words_per_line_mean:>5.1f}[/]  "
            f"[dim](med: {stats.words_per_line_median})[/]"
        )

    if rate_parts:
        console.print("  │  ".join(rate_parts))


def display_history_table(entries: List, base_dir: Path) -> None:
    """Display history results as a Rich table.

    Args:
        entries: List of HistoryEntry objects
        base_dir: Base directory for context in header
    """
    from core.history import HistoryEntry  # Import here to avoid circular

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Modified (PST)", style="dim", no_wrap=True, width=16)
    table.add_column("Ext", style="yellow", no_wrap=True, width=8)
    table.add_column("Path", style="cyan", no_wrap=False)
    table.add_column("Lines", justify="right", style="blue", width=7)
    table.add_column("Tokens", justify="right", style="magenta", width=8)

    # PST timezone
    pst = ZoneInfo("America/Los_Angeles")

    for entry in entries:
        # Convert timestamp to PST
        dt = datetime.fromtimestamp(entry.modified_date, tz=pst)
        date_str = dt.strftime("%y.%m.%d %H:%M")

        # Truncate long paths
        rel_path = entry.relative_path
        if len(rel_path) > 50:
            rel_path = "..." + rel_path[-47:]

        table.add_row(
            date_str,
            entry.extension,
            rel_path,
            f"{entry.lines:,}",
            f"{entry.tokens:,}",
        )

    # Display
    display_path = str(base_dir).replace(str(Path.home()), "~")
    console.print(f"\n[bold]Recent files in[/] [cyan]{display_path}[/] [dim]({len(entries)} shown)[/]\n")
    console.print(table)
    console.print()
