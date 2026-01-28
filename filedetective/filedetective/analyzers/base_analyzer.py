"""Base analyzer class for file analysis."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import statistics

from ..core.tokenizer import count_tokens


@dataclass
class FileStats:
    """Statistics for a file."""
    file_path: str
    file_type: str
    modified_date: float
    tokens: int
    lines: int
    chars: int
    words: Optional[int] = None  # For text files

    # Line range (if analyzing subset of file)
    line_start: Optional[int] = None  # 1-indexed, inclusive
    line_end: Optional[int] = None    # 1-indexed, inclusive
    total_lines: Optional[int] = None  # Total lines in file (when using range)

    # Rate calculations
    tokens_per_line_mean: Optional[float] = None
    tokens_per_line_median: Optional[int] = None
    words_per_line_mean: Optional[float] = None
    words_per_line_median: Optional[int] = None

    # Structure (for -o flag)
    structure: Optional[str] = None

    # Dependencies (for -d flag)
    dependencies: Optional[str] = None

    @property
    def has_line_range(self) -> bool:
        """Check if this analysis covers only a subset of lines."""
        return self.line_start is not None or self.line_end is not None

    @property
    def display_name(self) -> str:
        """Get display name (filename only)."""
        return Path(self.file_path).name

    @property
    def display_path(self) -> str:
        """Get display path with ~ for home."""
        return str(Path(self.file_path)).replace(str(Path.home()), "~")


@dataclass
class AggregateStats:
    """Aggregate statistics for multiple files."""
    file_count: int
    total_tokens: int
    total_lines: int
    total_chars: int
    total_words: Optional[int] = None
    individual_stats: list[FileStats] = None


class BaseAnalyzer(ABC):
    """Abstract base class for file analyzers."""

    def analyze(
        self,
        file_path: str,
        show_outline: bool = False,
        show_deps: bool = False,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> FileStats:
        """Analyze a file and return statistics.

        Args:
            file_path: Path to file
            show_outline: Whether to extract structure (TOC/functions)
            show_deps: Whether to extract dependencies
            line_start: Start line (1-indexed, inclusive). None = from beginning.
            line_end: End line (1-indexed, inclusive). None = to end.

        Returns:
            FileStats object with all requested information
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get all lines for potential slicing
        all_lines = content.splitlines()
        total_lines_in_file = len(all_lines)

        # Apply line range if specified
        has_range = line_start is not None or line_end is not None
        if has_range:
            # Convert to 0-indexed for slicing
            start_idx = (line_start - 1) if line_start else 0
            end_idx = line_end if line_end else total_lines_in_file

            # Clamp to valid range
            start_idx = max(0, min(start_idx, total_lines_in_file))
            end_idx = max(start_idx, min(end_idx, total_lines_in_file))

            # Slice lines and reconstruct content
            lines_list = all_lines[start_idx:end_idx]
            content = '\n'.join(lines_list)

            # Store actual range used (1-indexed for display)
            actual_start = start_idx + 1
            actual_end = end_idx
        else:
            lines_list = all_lines
            actual_start = None
            actual_end = None

        # Get basic stats
        stats = FileStats(
            file_path=file_path,
            file_type=self._get_type_name(),
            modified_date=Path(file_path).stat().st_mtime,
            tokens=count_tokens(content),
            lines=len(lines_list),
            chars=len(content),
            line_start=actual_start,
            line_end=actual_end,
            total_lines=total_lines_in_file if has_range else None,
        )

        # Calculate rates
        if stats.lines > 0:
            # Mean: total tokens / total lines
            stats.tokens_per_line_mean = stats.tokens / stats.lines

            # Median: per-line tokens for non-empty lines only
            tokens_per_line = []
            for line in lines_list:
                if line.strip():  # Skip empty lines
                    line_tokens = count_tokens(line)
                    tokens_per_line.append(line_tokens)

            if tokens_per_line:
                stats.tokens_per_line_median = round(statistics.median(tokens_per_line), 1)

        # Let subclasses add more specific stats
        self._analyze_specific(stats, content, show_outline, show_deps)

        return stats

    @abstractmethod
    def _get_type_name(self) -> str:
        """Get the type name for this analyzer."""
        pass

    @abstractmethod
    def _analyze_specific(
        self,
        stats: FileStats,
        content: str,
        show_outline: bool,
        show_deps: bool
    ) -> None:
        """Perform analyzer-specific analysis.

        Args:
            stats: FileStats object to populate
            content: File content
            show_outline: Whether to extract structure
            show_deps: Whether to extract dependencies
        """
        pass
