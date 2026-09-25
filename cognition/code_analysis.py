"""
Advanced Code Analysis & Generation Tool — code review, refactoring,
multi-language generation, complexity analysis, and documentation.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CodeIssue:
    severity: str
    category: str
    line: int
    message: str
    suggestion: str


@dataclass
class CodeAnalysis:
    file_path: str
    language: str
    lines_of_code: int = 0
    complexity: float = 0.0
    issues: list[CodeIssue] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)
    classes: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    maintainability_index: float = 100.0


class CodeAnalyzer:
    """Advanced static code analysis engine."""

    def analyze(self, code: str, file_path: str = "<string>", language: str = "python") -> CodeAnalysis:
        """Perform comprehensive code analysis."""
        result = CodeAnalysis(file_path=file_path, language=language)
        lines = code.split("\n")
        result.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        if language == "python":
            result = self._analyze_python(code, result)
        elif language in ("javascript", "typescript", "js", "ts"):
            result = self._analyze_javascript(code, result)
        else:
            result = self._analyze_generic(code, result)

        result.complexity = self._calculate_cyclomatic_complexity(code)
        result.maintainability_index = self._calculate_maintainability(result)

        return result

    def _analyze_python(self, code: str, result: CodeAnalysis) -> CodeAnalysis:
        """Analyze Python code."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.issues.append(
                CodeIssue("error", "syntax", e.lineno or 0, f"Syntax error: {e.msg}", "Fix syntax error")
            )
            return result

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result.functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": len(node.args.args),
                    "decorators": len(node.decorator_list),
                    "docstring": ast.get_docstring(node) is not None,
                })
                if not ast.get_docstring(node):
                    result.issues.append(
                        CodeIssue("info", "documentation", node.lineno,
                                  f"Function '{node.name}' lacks docstring",
                                  "Add a docstring to document the function")
                    )

            elif isinstance(node, ast.ClassDef):
                result.classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [ast.dump(b) for b in node.bases],
                    "docstring": ast.get_docstring(node) is not None,
                })
                if not ast.get_docstring(node):
                    result.issues.append(
                        CodeIssue("info", "documentation", node.lineno,
                                  f"Class '{node.name}' lacks docstring",
                                  "Add a docstring to document the class")
                    )

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        result.imports = imports

        code_lines = code.split("\n")
        for i, line in enumerate(code_lines, 1):
            stripped = line.strip()
            if len(stripped) > 120:
                result.issues.append(
                    CodeIssue("info", "style", i,
                              f"Line exceeds 120 characters ({len(stripped)} chars)",
                              "Break line or refactor")
                )

            if "except:" in stripped or "except Exception:" in stripped:
                result.issues.append(
                    CodeIssue("warning", "error_handling", i,
                              "Broad exception handler", "Catch specific exceptions")
                )

            if re.search(r'(password|secret|key|token)\s*=\s*["\']', stripped, re.IGNORECASE):
                result.issues.append(
                    CodeIssue("high", "security", i,
                              "Possible hardcoded credential",
                              "Use environment variable")
                )

        return result

    def _analyze_javascript(self, code: str, result: CodeAnalysis) -> CodeAnalysis:
        """Analyze JavaScript/TypeScript code."""
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if re.search(r'var\s+\w+', stripped):
                result.issues.append(
                    CodeIssue("info", "style", i,
                              "Use 'let' or 'const' instead of 'var'",
                              "Replace 'var' with 'let' or 'const'")
                )

            if re.search(r'==(?!=)', stripped) and "===" not in stripped:
                result.issues.append(
                    CodeIssue("warning", "style", i,
                              "Use strict equality (===) instead of loose equality (==)",
                              "Replace == with ===")
                )

            if "eval(" in stripped:
                result.issues.append(
                    CodeIssue("high", "security", i,
                              "eval() is a security risk",
                              "Avoid eval(); use safer alternatives")
                )

            if re.search(r'console\.(log|warn|error|debug)', stripped):
                result.issues.append(
                    CodeIssue("info", "quality", i,
                              "Console statement left in code",
                              "Remove console statements for production")
                )

            func_match = re.search(r'function\s+(\w+)', stripped)
            if func_match and not re.search(r'//.*function|/\*.*function', stripped):
                result.functions.append({
                    "name": func_match.group(1),
                    "line": i,
                    "docstring": False,
                })

        return result

    def _analyze_generic(self, code: str, result: CodeAnalysis) -> CodeAnalysis:
        """Generic analysis for any language."""
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if len(stripped) > 120:
                result.issues.append(
                    CodeIssue("info", "style", i,
                              f"Long line ({len(stripped)} chars)",
                              "Consider breaking the line")
                )
        return result

    def _calculate_cyclomatic_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity."""
        branching_keywords = [
            r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\bexcept\b', r'\bcatch\b', r'\bcase\b', r'\b\?\b', r'&&', r'\|\|',
        ]
        complexity = 1
        for pattern in branching_keywords:
            complexity += len(re.findall(pattern, code))
        return float(complexity)

    def _calculate_maintainability(self, result: CodeAnalysis) -> float:
        """Calculate maintainability index (0-100)."""
        score = 100.0

        score -= min(30, result.complexity * 2)
        score -= min(10, max(0, result.lines_of_code - 100) * 0.1)

        issue_penalties = {"error": 10, "high": 7, "warning": 4, "info": 1}
        for issue in result.issues:
            score -= issue_penalties.get(issue.severity, 1)

        functions_with_docs = sum(1 for f in result.functions if f.get("docstring"))
        total_functions = len(result.functions)
        if total_functions > 0:
            doc_coverage = functions_with_docs / total_functions
            score -= (1 - doc_coverage) * 10

        return max(0, min(100, score))


class CodeGenerator:
    """Generates code from descriptions with multi-language support."""

    def generate_function(
        self, description: str, language: str = "python", name: str = "generated_function"
    ) -> dict[str, str]:
        """Generate a function from description."""
        templates = {
            "python": self._python_function_template,
            "javascript": self._javascript_function_template,
            "typescript": self._typescript_function_template,
            "go": self._go_function_template,
            "rust": self._rust_function_template,
        }

        generator = templates.get(language, self._python_function_template)
        return {"language": language, "code": generator(description, name)}

    def _python_function_template(self, description: str, name: str) -> str:
        return f'''def {name}():
    """
    {description}

    Generated by AI Agent.
    """
    # Implementation based on: {description}
    pass
'''

    def _javascript_function_template(self, description: str, name: str) -> str:
        return f'''/**
 * {description}
 * Generated by AI Agent.
 */
function {name}() {{
    // Implementation based on: {description}
}}
'''

    def _typescript_function_template(self, description: str, name: str) -> str:
        return f'''/**
 * {description}
 * Generated by AI Agent.
 */
function {name}(): void {{
    // Implementation based on: {description}
}}
'''

    def _go_function_template(self, description: str, name: str) -> str:
        return f'''// {name} - {description}
// Generated by AI Agent.
func {name}() {{
    // Implementation based on: {description}
}}
'''

    def _rust_function_template(self, description: str, name: str) -> str:
        return f'''/// {description}
/// Generated by AI Agent.
fn {name}() {{
    // Implementation based on: {description}
}}
'''

    def generate_test(self, function_name: str, language: str = "python") -> dict[str, str]:
        """Generate test boilerplate."""
        if language == "python":
            code = f"""import unittest

class Test{function_name.title()}(unittest.TestCase):
    def test_basic_functionality(self):
        result = {function_name}()
        self.assertIsNotNone(result)

    def test_edge_cases(self):
        result = {function_name}()
        self.assertIsNotNone(result)

    def test_error_handling(self):
        with self.assertRaises(Exception):
            {function_name}(None)

if __name__ == "__main__":
    unittest.main()
"""
        else:
            code = f"// Test boilerplate for {function_name}"

        return {"language": language, "code": code}

    def refactor_suggestion(self, code: str, issue: str) -> str:
        """Generate refactoring suggestions."""
        suggestions = {
            "long_function": "Break this function into smaller, single-responsibility functions.",
            "duplicate_code": "Extract common logic into a shared utility function.",
            "deep_nesting": "Reduce nesting by using early returns or guard clauses.",
            "complex_condition": "Extract complex conditions into well-named boolean variables or functions.",
            "magic_number": "Replace magic numbers with named constants.",
            "long_parameter_list": "Group parameters into a config object or use keyword arguments.",
        }
        return suggestions.get(issue, f"Review code for: {issue}")
