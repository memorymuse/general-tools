"""Markdown file analyzer with TOC extraction."""
import re

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
        """Extract TOC if requested."""
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
