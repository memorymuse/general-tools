"""Base analyzer class for file analysis."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import statistics

from core.tokenizer import count_tokens


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
        show_deps: bool = False
    ) -> FileStats:
        """Analyze a file and return statistics.

        Args:
            file_path: Path to file
            show_outline: Whether to extract structure (TOC/functions)
            show_deps: Whether to extract dependencies

        Returns:
            FileStats object with all requested information
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get basic stats
        lines_list = content.splitlines()
        stats = FileStats(
            file_path=file_path,
            file_type=self._get_type_name(),
            modified_date=Path(file_path).stat().st_mtime,
            tokens=count_tokens(content),
            lines=len(lines_list),
            chars=len(content),
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
