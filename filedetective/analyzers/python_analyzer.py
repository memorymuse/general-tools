"""Python file analyzer with AST-based extraction.

Adapted from muse-codebase-mapper.py PythonAnalyzer class.
"""
import ast
from typing import Any, Dict, Optional

from analyzers.base_analyzer import BaseAnalyzer, FileStats


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python files using AST."""

    def _get_type_name(self) -> str:
        return "Python"

    def _analyze_specific(
        self,
        stats: FileStats,
        content: str,
        show_outline: bool,
        show_deps: bool
    ) -> None:
        """Extract structure and/or dependencies if requested."""
        try:
            tree = ast.parse(content)

            if show_outline:
                stats.structure = self._extract_structure(tree)

            if show_deps:
                stats.dependencies = self._extract_dependencies(tree)

        except SyntaxError as e:
            if show_outline:
                stats.structure = f"Syntax error on line {e.lineno}: {e.msg}"
            if show_deps:
                stats.dependencies = "Unable to parse file"

    def _extract_structure(self, tree: ast.AST) -> str:
        """Extract classes and functions with hierarchy.

        Args:
            tree: AST tree

        Returns:
            Formatted structure string
        """
        lines = []
        class_count = 0
        function_count = 0
        method_count = 0

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_count += 1
                lines.append(f"class {node.name}:")

                # Extract methods
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        is_async = isinstance(item, ast.AsyncFunctionDef)
                        async_prefix = "async " if is_async else ""
                        type_hint = self._get_return_type(item)
                        methods.append((item.name, item.lineno, async_prefix, type_hint))
                        method_count += 1

                # Format methods with tree structure
                for i, (name, lineno, async_prefix, type_hint) in enumerate(methods):
                    is_last = i == len(methods) - 1
                    prefix = "└──" if is_last else "├──"
                    hint_str = f" -> {type_hint}" if type_hint else ""
                    lines.append(f"  {prefix} {async_prefix}{name}(){hint_str} (Line {lineno})")

                if not methods:
                    lines.append("  └── (no methods)")

                lines.append("")  # Empty line after class

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Top-level function
                is_async = isinstance(node, ast.AsyncFunctionDef)
                async_prefix = "async " if is_async else ""
                type_hint = self._get_return_type(node)
                hint_str = f" -> {type_hint}" if type_hint else ""
                lines.append(f"{async_prefix}def {node.name}(){hint_str}: (Line {node.lineno})")
                lines.append("")
                function_count += 1

        # Summary
        if lines:
            summary = f"Summary: {class_count} classes, {method_count} methods, {function_count} standalone functions"
            lines.append(summary)
            return "\n".join(lines)
        else:
            return "No classes or functions found"

    def _extract_dependencies(self, tree: ast.AST) -> str:
        """Extract import statements.

        Args:
            tree: AST tree

        Returns:
            Formatted dependencies string
        """
        internal_imports = []
        external_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_internal_import(alias.name):
                        internal_imports.append(f"import {alias.name}")
                    else:
                        external_imports.append(f"import {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(alias.name for alias in node.names)
                import_str = f"from {module} import {names}"

                if self._is_internal_import(module):
                    internal_imports.append(import_str)
                else:
                    external_imports.append(import_str)

        lines = []

        if internal_imports:
            lines.append("Internal Dependencies:")
            for imp in internal_imports:
                lines.append(f"  {imp}")
            lines.append("")

        if external_imports:
            lines.append("External Dependencies:")
            for imp in external_imports:
                lines.append(f"  {imp}")

        if not lines:
            return "No imports found"

        return "\n".join(lines)

    def _get_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation as string.

        Args:
            node: Function definition node

        Returns:
            Return type string or None
        """
        if node.returns:
            return self._get_annotation(node.returns)
        return None

    def _get_annotation(self, node) -> str:
        """Get type annotation as string.

        Args:
            node: AST node representing type annotation

        Returns:
            Type annotation as string
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._get_annotation(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            slice_value = self._get_annotation(node.slice)
            return f"{value}[{slice_value}]"
        else:
            return "Any"

    def _is_internal_import(self, module_name: str) -> bool:
        """Check if import is internal (project) or external.

        Args:
            module_name: Module name from import

        Returns:
            True if internal, False if external/stdlib
        """
        # List of common stdlib modules (partial list)
        stdlib = {
            "os", "sys", "re", "json", "ast", "typing", "pathlib",
            "collections", "dataclasses", "datetime", "time", "math",
            "random", "itertools", "functools", "operator", "copy",
            "io", "csv", "sqlite3", "pickle", "shelve", "dbm",
            "argparse", "logging", "unittest", "pytest", "asyncio",
            "concurrent", "threading", "multiprocessing", "subprocess",
            "socket", "http", "urllib", "email", "xml", "html",
        }

        if not module_name:
            return False

        # Get first part of module name
        first_part = module_name.split('.')[0]

        # Check if it's stdlib or common external package
        if first_part in stdlib:
            return False

        # Common external packages
        if first_part in {"pydantic", "fastapi", "flask", "django", "numpy", "pandas", "requests", "aiohttp"}:
            return False

        # Assume anything else is internal
        return True
