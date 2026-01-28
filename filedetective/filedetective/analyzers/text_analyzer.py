"""Text file analyzer."""
from .base_analyzer import BaseAnalyzer, FileStats


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
        """Text files have no special analysis beyond base stats."""
        pass
