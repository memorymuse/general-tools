"""File analysis dispatcher."""
from typing import List, Optional

from ..analyzers.base_analyzer import FileStats, AggregateStats
from ..analyzers.text_analyzer import TextAnalyzer
from ..analyzers.markdown_analyzer import MarkdownAnalyzer
from ..analyzers.python_analyzer import PythonAnalyzer
from ..analyzers.javascript_analyzer import JavaScriptAnalyzer
from ..utils.file_utils import FileType, detect_file_type, validate_file_types


class FileAnalyzer:
    """Dispatches file analysis to appropriate analyzer."""

    def __init__(self):
        """Initialize analyzers."""
        js_analyzer = JavaScriptAnalyzer()
        self.analyzers = {
            FileType.TEXT: TextAnalyzer(),
            FileType.MARKDOWN: MarkdownAnalyzer(),
            FileType.PYTHON: PythonAnalyzer(),
            FileType.JAVASCRIPT: js_analyzer,
            FileType.TYPESCRIPT: js_analyzer,  # Same analyzer for both
        }

    def analyze_file(
        self,
        file_path: str,
        show_outline: bool = False,
        show_deps: bool = False
    ) -> FileStats:
        """Analyze a single file.

        Args:
            file_path: Path to file
            show_outline: Whether to extract structure
            show_deps: Whether to extract dependencies

        Returns:
            FileStats object

        Raises:
            ValueError: If file type not supported or invalid flag combo
        """
        file_type = detect_file_type(file_path)

        # Validate flags
        if show_deps and not file_type.is_code:
            raise ValueError(
                f"-d (--deps) flag only applies to code files.\n"
                f"  {file_path} is type: {file_type.value}\n"
                f"Try -o (--outline) for table of contents."
            )

        # Get analyzer
        analyzer = self.analyzers.get(file_type)
        if analyzer is None:
            raise ValueError(f"Unsupported file type: {file_type.value}")

        # Analyze
        return analyzer.analyze(file_path, show_outline, show_deps)

    def analyze_multiple(
        self,
        file_paths: List[str],
        show_outline: bool = False,
        show_deps: bool = False
    ) -> AggregateStats:
        """Analyze multiple files.

        Args:
            file_paths: List of file paths
            show_outline: Whether to extract structure
            show_deps: Whether to extract dependencies

        Returns:
            AggregateStats object

        Raises:
            ValueError: If files are mixed types or invalid flags
        """
        # Validate all files are same type
        is_valid, error_msg = validate_file_types(file_paths)
        if not is_valid:
            raise ValueError(error_msg)

        # Analyze each file
        individual_stats = []
        for file_path in file_paths:
            try:
                stats = self.analyze_file(file_path, show_outline, show_deps)
                individual_stats.append(stats)
            except Exception as e:
                # Skip files that fail analysis
                print(f"Warning: Skipped {file_path}: {e}")
                continue

        if not individual_stats:
            raise ValueError("No files could be analyzed")

        # Calculate aggregates
        total_tokens = sum(s.tokens for s in individual_stats)
        total_lines = sum(s.lines for s in individual_stats)
        total_chars = sum(s.chars for s in individual_stats)

        # Word count (if text files)
        total_words = None
        if any(s.words is not None for s in individual_stats):
            total_words = sum(s.words for s in individual_stats if s.words is not None)

        return AggregateStats(
            file_count=len(individual_stats),
            total_tokens=total_tokens,
            total_lines=total_lines,
            total_chars=total_chars,
            total_words=total_words,
            individual_stats=individual_stats
        )
