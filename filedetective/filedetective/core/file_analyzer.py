"""File analysis dispatcher."""
from typing import List, Optional, Tuple

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
        show_deps: bool = False,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None
    ) -> FileStats:
        """Analyze a single file.

        Args:
            file_path: Path to file
            show_outline: Whether to extract structure
            show_deps: Whether to extract dependencies
            line_start: Start line (1-indexed, inclusive). None = from beginning.
            line_end: End line (1-indexed, inclusive). None = to end.

        Returns:
            FileStats object

        Raises:
            ValueError: If file type not supported or invalid flag combo
        """
        file_type = detect_file_type(file_path)

        # Gracefully handle -d flag for non-code files
        # (dependencies will simply be None for these file types)
        effective_show_deps = show_deps and file_type.is_code

        # Get analyzer - fallback to TextAnalyzer for unsupported types
        # This allows analyzing any text-based file (XML, YAML, TOML, etc.)
        analyzer = self.analyzers.get(file_type)
        if analyzer is None:
            analyzer = self.analyzers[FileType.TEXT]

        # Analyze
        return analyzer.analyze(
            file_path, show_outline, effective_show_deps,
            line_start=line_start, line_end=line_end
        )

    def analyze_multiple(
        self,
        file_specs: List[Tuple[str, Optional[int], Optional[int]]],
        show_outline: bool = False,
        show_deps: bool = False
    ) -> AggregateStats:
        """Analyze multiple files.

        Args:
            file_specs: List of (file_path, line_start, line_end) tuples.
                       line_start/line_end can be None for full file.
            show_outline: Whether to extract structure
            show_deps: Whether to extract dependencies

        Returns:
            AggregateStats object

        Raises:
            ValueError: If no files could be analyzed
        """
        # Extract just the file paths for validation
        file_paths = [spec[0] for spec in file_specs]

        # Note: Mixed file types are allowed - all text-based files can be analyzed
        is_valid, error_msg = validate_file_types(file_paths)
        if not is_valid:
            raise ValueError(error_msg)

        # Analyze each file
        individual_stats = []
        for file_path, line_start, line_end in file_specs:
            try:
                stats = self.analyze_file(
                    file_path, show_outline, show_deps,
                    line_start=line_start, line_end=line_end
                )
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
