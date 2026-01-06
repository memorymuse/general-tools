"""Markdown file analyzer with TOC extraction."""
import re
import statistics

from .base_analyzer import BaseAnalyzer, FileStats


class MarkdownAnalyzer(BaseAnalyzer):
    """Analyzer for Markdown files."""

    def _get_type_name(self) -> str:
        return "Markdown"

    def _analyze_specific(
        self,
        stats: FileStats,
        content: str,
        show_outline: bool,
        show_deps: bool
    ) -> None:
        """Add word count and optionally TOC."""
        # Count words (like text)
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

        # Extract TOC if requested
        if show_outline:
            stats.structure = self._extract_toc(content)

    def _extract_toc(self, content: str) -> str:
        """Extract table of contents from markdown headers.

        Args:
            content: Markdown content

        Returns:
            Formatted TOC string
        """
        lines = content.splitlines()
        toc_entries = []

        # Pattern: ^(#{1,6})\s+(.+)$
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        for line_num, line in enumerate(lines, start=1):
            match = header_pattern.match(line)
            if match:
                hashes, text = match.groups()
                level = len(hashes)
                indent = "  " * (level - 1)
                toc_entries.append(f"{indent}{line} (Line {line_num})")

        if toc_entries:
            return "Table of Contents:\n" + "\n".join(toc_entries)
        else:
            return "No headers found"
