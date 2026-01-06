"""JavaScript/TypeScript file analyzer with regex-based extraction.

Supports .js, .jsx, .ts, .tsx files.
Uses pragmatic regex patterns for structure and dependency extraction.
"""
import re
from typing import Optional, List, Tuple

from .base_analyzer import BaseAnalyzer, FileStats


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzer for JavaScript and TypeScript files."""

    def _get_type_name(self) -> str:
        return "JavaScript/TypeScript"

    def _analyze_specific(
        self,
        stats: FileStats,
        content: str,
        show_outline: bool,
        show_deps: bool
    ) -> None:
        """Extract structure and/or dependencies if requested."""
        if show_outline:
            stats.structure = self._extract_structure(content)

        if show_deps:
            stats.dependencies = self._extract_dependencies(content)

    def _extract_structure(self, content: str) -> str:
        """Extract functions and classes with hierarchy.

        Args:
            content: File content

        Returns:
            Formatted structure string
        """
        lines = []
        class_count = 0
        function_count = 0
        method_count = 0

        # Split into lines for line number tracking
        content_lines = content.splitlines()

        # Extract classes with their methods
        classes = self._find_classes(content_lines)
        for class_name, class_line, methods in classes:
            class_count += 1
            lines.append(f"class {class_name}:")

            if methods:
                for i, (method_name, method_line, is_async, is_static) in enumerate(methods):
                    is_last = i == len(methods) - 1
                    prefix = "└──" if is_last else "├──"

                    modifiers = []
                    if is_static:
                        modifiers.append("static")
                    if is_async:
                        modifiers.append("async")

                    modifier_str = " ".join(modifiers)
                    if modifier_str:
                        modifier_str += " "

                    lines.append(f"  {prefix} {modifier_str}{method_name}() (Line {method_line})")
                    method_count += 1
            else:
                lines.append("  └── (no methods)")

            lines.append("")  # Empty line after class

        # Extract standalone functions
        functions = self._find_functions(content_lines, exclude_classes=classes)
        for func_name, func_line, is_async, is_arrow in functions:
            async_prefix = "async " if is_async else ""
            arrow_suffix = " =>" if is_arrow else ""
            lines.append(f"{async_prefix}function {func_name}(){arrow_suffix} (Line {func_line})")
            lines.append("")
            function_count += 1

        # Summary
        if lines:
            summary = f"Summary: {class_count} classes, {method_count} methods, {function_count} standalone functions"
            lines.append(summary)
            return "\n".join(lines)
        else:
            return "No classes or functions found"

    def _find_classes(self, lines: List[str]) -> List[Tuple[str, int, List[Tuple[str, int, bool, bool]]]]:
        """Find all classes and their methods.

        Args:
            lines: File lines

        Returns:
            List of (class_name, line_number, methods) tuples
            where methods is List of (method_name, line_num, is_async, is_static)
        """
        classes = []

        # Pattern: class ClassName or export class ClassName
        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)')

        i = 0
        while i < len(lines):
            match = class_pattern.match(lines[i])
            if match:
                class_name = match.group(1)
                class_line = i + 1

                # Find methods in this class (look ahead until next class or end)
                methods = []
                j = i
                brace_count = 0

                while j < len(lines):
                    line = lines[j]

                    # Look for methods BEFORE adjusting brace count
                    # Pattern: methodName() or async methodName()
                    # Handles TypeScript return types: method(): Type {
                    method_match = re.match(r'^\s*(static\s+)?(async\s+)?(\w+)\s*\([^)]*\)(?::\s*[^{]+)?\s*{', line)
                    if method_match and j > i:  # Don't match the class line itself
                        is_static = method_match.group(1) is not None
                        is_async = method_match.group(2) is not None
                        method_name = method_match.group(3)
                        methods.append((method_name, j + 1, is_async, is_static))

                    # Track braces to know when class ends
                    brace_count += line.count('{') - line.count('}')

                    # If we've closed all braces and started with at least one, class is done
                    if j > i and brace_count <= 0:
                        break

                    j += 1

                classes.append((class_name, class_line, methods))
                i = j
            else:
                i += 1

        return classes

    def _find_functions(
        self,
        lines: List[str],
        exclude_classes: List[Tuple[str, int, List]]
    ) -> List[Tuple[str, int, bool, bool]]:
        """Find standalone functions (not inside classes).

        Args:
            lines: File lines
            exclude_classes: Classes to exclude (to avoid counting methods)

        Returns:
            List of (func_name, line_num, is_async, is_arrow) tuples
        """
        functions = []

        # Get line numbers to exclude (inside classes)
        # We need to re-scan to find exact class boundaries
        exclude_lines = set()
        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)')

        for i, line in enumerate(lines):
            if class_pattern.match(line):
                # Found a class, track braces to find where it ends
                j = i
                brace_count = 0
                while j < len(lines):
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    exclude_lines.add(j + 1)  # Mark as line number (1-indexed)
                    if j > i and brace_count <= 0:
                        break
                    j += 1

        # Pattern 1: function foo() or async function foo()
        # Handles generics: function foo<T>()
        func_pattern = re.compile(r'^\s*(?:export\s+)?(async\s+)?function\s+(\w+)(?:<[^>]+>)?\s*\(')

        # Pattern 2: const foo = async () => or const foo = () =>
        # Handles TypeScript return types: const foo = (): Type =>
        arrow_pattern = re.compile(r'^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)(?::\s*[^=]+)?\s*=>')

        for i, line in enumerate(lines):
            line_num = i + 1

            # Skip if inside a class
            if line_num in exclude_lines:
                continue

            # Check function declaration
            match = func_pattern.match(line)
            if match:
                is_async = match.group(1) is not None
                func_name = match.group(2)
                functions.append((func_name, line_num, is_async, False))
                continue

            # Check arrow function
            match = arrow_pattern.match(line)
            if match:
                func_name = match.group(1)
                is_async = match.group(2) is not None
                functions.append((func_name, line_num, is_async, True))

        return functions

    def _extract_dependencies(self, content: str) -> str:
        """Extract import/require statements.

        Args:
            content: File content

        Returns:
            Formatted dependencies string
        """
        internal_imports = []
        external_imports = []

        lines = content.splitlines()

        for line in lines:
            line = line.strip()

            # ES6 imports: import X from 'module'
            es6_match = re.match(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', line)
            if es6_match:
                module = es6_match.group(1)
                if self._is_internal_import(module):
                    internal_imports.append(line)
                else:
                    external_imports.append(line)
                continue

            # ES6 side-effect imports: import 'module' (no from clause)
            side_effect_match = re.match(r'import\s+[\'"]([^\'"]+)[\'"]', line)
            if side_effect_match:
                module = side_effect_match.group(1)
                if self._is_internal_import(module):
                    internal_imports.append(line)
                else:
                    external_imports.append(line)
                continue

            # CommonJS: require('module')
            require_match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', line)
            if require_match:
                module = require_match.group(1)
                if self._is_internal_import(module):
                    internal_imports.append(line)
                else:
                    external_imports.append(line)
                continue

        result_lines = []

        if internal_imports:
            result_lines.append("Internal Dependencies:")
            for imp in internal_imports:
                result_lines.append(f"  {imp}")
            result_lines.append("")

        if external_imports:
            result_lines.append("External Dependencies:")
            for imp in external_imports:
                result_lines.append(f"  {imp}")

        if not result_lines:
            return "No imports found"

        return "\n".join(result_lines)

    def _is_internal_import(self, module_path: str) -> bool:
        """Check if import is internal (project) or external.

        Args:
            module_path: Module path from import

        Returns:
            True if internal, False if external
        """
        # Internal if starts with ./ or ../ or @/
        if module_path.startswith(('./')) or module_path.startswith('../') or module_path.startswith('@/'):
            return True

        # Otherwise external (npm package)
        return False
