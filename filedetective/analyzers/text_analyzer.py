"""Text file analyzer."""
import statistics

from analyzers.base_analyzer import BaseAnalyzer, FileStats


class TextAnalyzer(BaseAnalyzer):
    """Analyzer for plain text files."""

    def _get_type_name(self) -> str:
        return "Text"

    def _analyze_specific(
        self,
        stats: FileStats,
        content: str,
        show_outline: bool,
        show_deps: bool
    ) -> None:
        """Add word count and word-per-line rates."""
        # Count words
        stats.words = len(content.split())

        # Calculate words per line
        if stats.lines > 0:
            # Mean: total words / total lines
            stats.words_per_line_mean = stats.words / stats.lines

            # Median: per-line words for non-empty lines only
            lines = content.splitlines()
            words_per_line = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    words_per_line.append(len(line.split()))

            if words_per_line:
                stats.words_per_line_median = round(statistics.median(words_per_line), 1)
