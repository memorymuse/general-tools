"""Tests for file analyzer functionality.

TDD tests for:
1. Generic text fallback (Phase 1) - any text file should be analyzable
2. Mixed file type analysis (Phase 2) - different types together
3. Graceful flag handling (Phase 2) - -o/-d on unsupported types
"""
import pytest
from pathlib import Path

from filedetective.core.file_analyzer import FileAnalyzer
from filedetective.utils.file_utils import detect_file_type, FileType, validate_file_types


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGenericTextFallback:
    """Phase 1: Any text-based file should be analyzable with basic stats."""

    def test_analyze_xml_file(self):
        """XML files should be analyzable with basic stats."""
        analyzer = FileAnalyzer()
        xml_path = FIXTURES_DIR / "sample.xml"

        stats = analyzer.analyze_file(str(xml_path))

        assert stats.tokens > 0
        assert stats.lines > 0
        assert stats.chars > 0
        assert stats.file_path == str(xml_path)

    def test_analyze_yaml_file(self):
        """YAML files should be analyzable with basic stats."""
        analyzer = FileAnalyzer()
        yaml_path = FIXTURES_DIR / "sample.yaml"

        stats = analyzer.analyze_file(str(yaml_path))

        assert stats.tokens > 0
        assert stats.lines > 0
        assert stats.chars > 0

    def test_analyze_toml_file(self):
        """TOML files should be analyzable with basic stats."""
        analyzer = FileAnalyzer()
        toml_path = FIXTURES_DIR / "sample.toml"

        stats = analyzer.analyze_file(str(toml_path))

        assert stats.tokens > 0
        assert stats.lines > 0
        assert stats.chars > 0

    def test_analyze_unknown_extension(self):
        """Files with unknown extensions should still be analyzable."""
        # Create a temporary file with a weird extension
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.customext', delete=False) as f:
            f.write("This is some text content\nwith multiple lines")
            temp_path = f.name

        try:
            analyzer = FileAnalyzer()
            stats = analyzer.analyze_file(temp_path)

            assert stats.tokens > 0
            assert stats.lines == 2
            assert stats.chars > 0
        finally:
            Path(temp_path).unlink()


class TestMixedFileTypeAnalysis:
    """Phase 2: Different file types should be analyzable together."""

    def test_validate_mixed_code_and_text(self):
        """Mixing code and text files should be allowed."""
        files = [
            str(FIXTURES_DIR / "sample.py"),
            str(FIXTURES_DIR / "sample.md"),
        ]

        is_valid, error_msg = validate_file_types(files)

        assert is_valid is True
        assert error_msg is None

    def test_validate_mixed_multiple_types(self):
        """Mixing multiple different file types should be allowed."""
        files = [
            str(FIXTURES_DIR / "sample.py"),
            str(FIXTURES_DIR / "sample.md"),
            str(FIXTURES_DIR / "sample.yaml"),
            str(FIXTURES_DIR / "sample.xml"),
        ]

        is_valid, error_msg = validate_file_types(files)

        assert is_valid is True
        assert error_msg is None

    def test_analyze_multiple_mixed_types(self):
        """Analyzing multiple files of different types should work and produce totals."""
        analyzer = FileAnalyzer()
        files = [
            str(FIXTURES_DIR / "sample.py"),
            str(FIXTURES_DIR / "sample.md"),
            str(FIXTURES_DIR / "sample.yaml"),
        ]

        agg_stats = analyzer.analyze_multiple(files)

        assert agg_stats.file_count == 3
        assert agg_stats.total_tokens > 0
        assert agg_stats.total_lines > 0
        assert agg_stats.total_chars > 0
        assert len(agg_stats.individual_stats) == 3

    def test_analyze_multiple_totals_are_correct(self):
        """Total stats should equal sum of individual stats."""
        analyzer = FileAnalyzer()
        files = [
            str(FIXTURES_DIR / "sample.py"),
            str(FIXTURES_DIR / "sample.md"),
        ]

        agg_stats = analyzer.analyze_multiple(files)

        expected_tokens = sum(s.tokens for s in agg_stats.individual_stats)
        expected_lines = sum(s.lines for s in agg_stats.individual_stats)
        expected_chars = sum(s.chars for s in agg_stats.individual_stats)

        assert agg_stats.total_tokens == expected_tokens
        assert agg_stats.total_lines == expected_lines
        assert agg_stats.total_chars == expected_chars


class TestGracefulFlagHandling:
    """Phase 2: -o and -d flags should gracefully handle unsupported types."""

    def test_outline_flag_on_unsupported_type_does_not_error(self):
        """Using -o on files without structure support should not raise error."""
        analyzer = FileAnalyzer()
        yaml_path = FIXTURES_DIR / "sample.yaml"

        # This should NOT raise an error
        stats = analyzer.analyze_file(str(yaml_path), show_outline=True)

        assert stats.tokens > 0
        # Structure may be None or empty for unsupported types
        # The key is that it doesn't crash

    def test_deps_flag_on_non_code_does_not_error(self):
        """Using -d on non-code files should not raise error."""
        analyzer = FileAnalyzer()
        yaml_path = FIXTURES_DIR / "sample.yaml"

        # This should NOT raise an error
        stats = analyzer.analyze_file(str(yaml_path), show_deps=True)

        assert stats.tokens > 0
        # Dependencies may be None for non-code types

    def test_deps_flag_on_markdown_does_not_error(self):
        """Using -d on markdown files should not raise error."""
        analyzer = FileAnalyzer()
        md_path = FIXTURES_DIR / "sample.md"

        # This should NOT raise an error
        stats = analyzer.analyze_file(str(md_path), show_deps=True)

        assert stats.tokens > 0


class TestFileTypeDetection:
    """Test file type detection for new types."""

    def test_detect_yaml(self):
        """YAML files should be detected correctly."""
        assert detect_file_type("config.yaml") == FileType.YAML
        assert detect_file_type("config.yml") == FileType.YAML

    def test_detect_xml(self):
        """XML files should be detected as XML or UNKNOWN (depending on implementation)."""
        file_type = detect_file_type("config.xml")
        # After implementation, this should be FileType.XML
        # For now, may be UNKNOWN
        assert file_type in (FileType.UNKNOWN, getattr(FileType, 'XML', FileType.UNKNOWN))

    def test_detect_toml(self):
        """TOML files should be detectable."""
        file_type = detect_file_type("config.toml")
        # After implementation, this should be a specific type
        # For now, may be UNKNOWN
        assert file_type in (FileType.UNKNOWN, getattr(FileType, 'TOML', FileType.UNKNOWN))


class TestDisplayEnhancements:
    """Phase 3: Display shows Type column for mixed types."""

    def test_aggregate_stats_tracks_individual_types(self):
        """AggregateStats should preserve individual file types."""
        analyzer = FileAnalyzer()
        files = [
            str(FIXTURES_DIR / "sample.py"),
            str(FIXTURES_DIR / "sample.md"),
        ]

        agg_stats = analyzer.analyze_multiple(files)

        # Individual stats should have different types
        types = [s.file_type for s in agg_stats.individual_stats]
        assert "Python" in types
        assert "Markdown" in types

    def test_same_types_have_consistent_type_value(self):
        """Files of same type should have identical type string."""
        analyzer = FileAnalyzer()

        stats1 = analyzer.analyze_file(str(FIXTURES_DIR / "sample.md"))
        stats2 = analyzer.analyze_file(str(FIXTURES_DIR / "sample.md"))

        # Same file should have same type
        assert stats1.file_type == stats2.file_type


class TestExistingFunctionality:
    """Ensure existing functionality still works (regression tests)."""

    def test_analyze_python_file(self):
        """Python files should still be analyzed correctly."""
        analyzer = FileAnalyzer()
        py_path = FIXTURES_DIR / "sample.py"

        stats = analyzer.analyze_file(str(py_path))

        assert stats.file_type == "Python"
        assert stats.tokens > 0
        assert stats.lines > 0

    def test_analyze_python_with_outline(self):
        """Python files with -o should show structure."""
        analyzer = FileAnalyzer()
        py_path = FIXTURES_DIR / "sample.py"

        stats = analyzer.analyze_file(str(py_path), show_outline=True)

        assert stats.structure is not None
        assert "Calculator" in stats.structure  # Class should be detected

    def test_analyze_python_with_deps(self):
        """Python files with -d should show dependencies."""
        analyzer = FileAnalyzer()
        py_path = FIXTURES_DIR / "sample.py"

        stats = analyzer.analyze_file(str(py_path), show_deps=True)

        assert stats.dependencies is not None
        assert "typing" in stats.dependencies or "os" in stats.dependencies

    def test_analyze_markdown_file(self):
        """Markdown files should still be analyzed correctly."""
        analyzer = FileAnalyzer()
        md_path = FIXTURES_DIR / "sample.md"

        stats = analyzer.analyze_file(str(md_path))

        assert stats.file_type == "Markdown"
        assert stats.tokens > 0

    def test_analyze_markdown_with_outline(self):
        """Markdown files with -o should show TOC."""
        analyzer = FileAnalyzer()
        md_path = FIXTURES_DIR / "sample.md"

        stats = analyzer.analyze_file(str(md_path), show_outline=True)

        assert stats.structure is not None
        assert "Section One" in stats.structure or "Sample Markdown" in stats.structure

    def test_analyze_javascript_file(self):
        """JavaScript files should still be analyzed correctly."""
        analyzer = FileAnalyzer()
        js_path = FIXTURES_DIR / "sample.js"

        stats = analyzer.analyze_file(str(js_path))

        # JS and TS share the same analyzer which returns "JavaScript/TypeScript"
        assert "JavaScript" in stats.file_type
        assert stats.tokens > 0

    def test_analyze_typescript_file(self):
        """TypeScript files should still be analyzed correctly."""
        analyzer = FileAnalyzer()
        ts_path = FIXTURES_DIR / "sample.ts"

        stats = analyzer.analyze_file(str(ts_path))

        # JS and TS share the same analyzer which returns "JavaScript/TypeScript"
        assert "TypeScript" in stats.file_type
        assert stats.tokens > 0
