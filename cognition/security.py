"""
Security Audit Tool — scans codebases for vulnerabilities,
checks configurations, and performs security analysis.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Vulnerability:
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: str = ""


@dataclass
class AuditResult:
    target: str
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    score: float = 100.0
    summary: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.summary = {
            "critical": sum(1 for v in self.vulnerabilities if v.severity == "critical"),
            "high": sum(1 for v in self.vulnerabilities if v.severity == "high"),
            "medium": sum(1 for v in self.vulnerabilities if v.severity == "medium"),
            "low": sum(1 for v in self.vulnerabilities if v.severity == "low"),
            "info": sum(1 for v in self.vulnerabilities if v.severity == "info"),
        }
        penalty = (
            self.summary["critical"] * 25
            + self.summary["high"] * 15
            + self.summary["medium"] * 8
            + self.summary["low"] * 3
        )
        self.score = max(0, 100 - penalty)


class SecurityAuditor:
    """Comprehensive security auditing engine."""

    def __init__(self) -> None:
        self._rules = self._load_rules()

    def _load_rules(self) -> dict[str, dict[str, Any]]:
        return {
            "sql_injection": {
                "severity": "critical",
                "category": "injection",
                "cwe": "CWE-89",
                "pattern": r'(execute|cursor\.execute|query|raw)\s*\(\s*[f"\'].*(%s|{|\+)',
                "description": "Potential SQL injection vulnerability",
                "recommendation": "Use parameterized queries instead of string formatting",
            },
            "fstring_sql": {
                "severity": "critical",
                "category": "injection",
                "cwe": "CWE-89",
                "pattern": r'\bf["\'][^\'"]*\b(SELECT\s|INSERT\sINTO|UPDATE\s|DELETE\sFROM|DROP\s|ALTER\s|CREATE\s|TRUNCATE\b)[^\'"]*(\{|\+|%)',
                "description": "SQL query built via f-string interpolation allows injection",
                "recommendation": "Use parameterized queries instead of f-string SQL",
            },
            "xss": {
                "severity": "high",
                "category": "xss",
                "cwe": "CWE-79",
                "pattern": r'(innerHTML|document\.write|\.html\(|v-html)',
                "description": "Potential XSS vulnerability via unescaped HTML",
                "recommendation": "Sanitize and escape user input before rendering",
            },
            "hardcoded_secret": {
                "severity": "critical",
                "category": "secrets",
                "cwe": "CWE-798",
                "pattern": r'(password|secret_key|api_key|apikey|private_key)\s*=\s*["\'][A-Za-z0-9+/]{8,}["\']',
                "description": "Hardcoded secret or credential detected",
                "recommendation": "Use environment variables or a secrets manager",
            },
            "weak_crypto": {
                "severity": "high",
                "category": "cryptography",
                "cwe": "CWE-327",
                "pattern": r'(md5|sha1|des)\s*\(',
                "description": "Weak cryptographic algorithm in use",
                "recommendation": "Use SHA-256+ or AES for encryption/hashing",
            },
            "eval_exec": {
                "severity": "critical",
                "category": "code_injection",
                "cwe": "CWE-95",
                "pattern": r'(eval|exec|compile)\s*\(',
                "description": "Dynamic code execution detected",
                "recommendation": "Avoid eval/exec; use safer alternatives like ast.literal_eval",
            },
            "path_traversal": {
                "severity": "high",
                "category": "path_traversal",
                "cwe": "CWE-22",
                "pattern": r'(open|Path)\s*\(\s*.*(\+|format|f["\'])',
                "description": "Potential path traversal vulnerability",
                "recommendation": "Validate and sanitize file paths, use os.path.realpath",
            },
            "insecure_random": {
                "severity": "medium",
                "category": "cryptography",
                "cwe": "CWE-330",
                "pattern": r'random\.(random|randint|choice|sample)\s*\(',
                "description": "Non-cryptographic random number generator",
                "recommendation": "Use secrets module for security-sensitive randomness",
            },
            "debug_enabled": {
                "severity": "medium",
                "category": "configuration",
                "cwe": "CWE-489",
                "pattern": r'(DEBUG\s*=\s*True|debug\s*=\s*True)',
                "description": "Debug mode is enabled",
                "recommendation": "Disable debug mode in production",
            },
            "cors_wildcard": {
                "severity": "high",
                "category": "configuration",
                "cwe": "CWE-942",
                "pattern": r'(Access-Control-Allow-Origin|allow_origins)\s*[=:]\s*["\']*[\*]',
                "description": "CORS wildcard allows all origins",
                "recommendation": "Restrict CORS to specific trusted origins",
            },
            "insecure_http": {
                "severity": "medium",
                "category": "transport",
                "cwe": "CWE-319",
                "pattern": r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)',
                "description": "Insecure HTTP endpoint (not HTTPS)",
                "recommendation": "Use HTTPS for all network communications",
            },
            "unused_import": {
                "severity": "info",
                "category": "code_quality",
                "cwe": "",
                "pattern": None,
                "description": "Unused imports increase attack surface",
                "recommendation": "Remove unused imports",
            },
            "bare_except": {
                "severity": "low",
                "category": "error_handling",
                "cwe": "CWE-396",
                "pattern": r'except\s*:',
                "description": "Bare except clause catches all exceptions including SystemExit",
                "recommendation": "Catch specific exceptions (except Exception: at minimum)",
            },
            "pickle_load": {
                "severity": "high",
                "category": "deserialization",
                "cwe": "CWE-502",
                "pattern": r'pickle\.(loads?|Unpickler)',
                "description": "Unsafe pickle deserialization",
                "recommendation": "Avoid pickle for untrusted data; use JSON instead",
            },
            "eval_in_request": {
                "severity": "critical",
                "category": "code_injection",
                "cwe": "CWE-95",
                "pattern": r'(request\.(args|form|data|json)\[|input\s*\([^)]*\))',
                "description": "User input may reach eval/exec",
                "recommendation": "Never pass user input to eval/exec",
            },
        }

    def _is_in_string(self, line: str, match_start: int) -> bool:
        """Check if a character position is inside a string literal."""
        in_single = False
        in_double = False
        escape_next = False
        for i, ch in enumerate(line):
            if i >= match_start:
                break
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
        return in_single or in_double

    def audit_code(self, code: str, file_path: str = "<string>") -> AuditResult:
        """Audit a code string for security vulnerabilities."""
        result = AuditResult(target=file_path)
        lines = code.split("\n")

        # Track if we're inside a multi-line string
        in_docstring = False
        in_triple_quote = False

        for rule_name, rule in self._rules.items():
            if rule["pattern"] is None:
                continue

            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Skip comments
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue

                # Track multi-line strings / docstrings
                triple_count = stripped.count('"""') + stripped.count("'''")
                if triple_count % 2 == 1:
                    in_triple_quote = not in_triple_quote
                if in_triple_quote:
                    continue

                # Skip lines that are clearly string content
                if stripped.startswith('"') or stripped.startswith("'"):
                    continue

                # Skip lines that are just describing the pattern (in rule definitions)
                if file_path == "<string>" and 'description' in line:
                    continue

                match = re.search(rule["pattern"], line)
                if match:
                    # Skip if the match is inside a string literal
                    if self._is_in_string(line, match.start()):
                        continue

                    snippet_start = max(0, i - 2)
                    snippet_end = min(len(lines), i + 1)
                    snippet = "\n".join(
                        f"  {j + 1}: {lines[j]}" for j in range(snippet_start, snippet_end)
                    )

                    vuln = Vulnerability(
                        severity=rule["severity"],
                        category=rule["category"],
                        title=rule_name.replace("_", " ").title(),
                        description=rule["description"],
                        file_path=file_path,
                        line_number=i,
                        code_snippet=snippet,
                        recommendation=rule["recommendation"],
                        cwe_id=rule["cwe"],
                    )
                    result.vulnerabilities.append(vuln)

        result.vulnerabilities.sort(
            key=lambda v: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}[v.severity]
        )

        return result

    def audit_file(self, file_path: str) -> AuditResult:
        """Audit a file on disk."""
        p = Path(file_path)
        if not p.exists():
            return AuditResult(
                target=file_path,
                warnings=[f"File not found: {file_path}"],
            )

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            return self.audit_code(content, file_path)
        except Exception as e:
            return AuditResult(
                target=file_path,
                warnings=[f"Error reading file: {e}"],
            )

    def audit_directory(self, directory: str, extensions: list[str] | None = None) -> list[AuditResult]:
        """Audit all code files in a directory."""
        exts = extensions or [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".php"]
        results: list[AuditResult] = []
        root = Path(directory)

        if not root.exists():
            return [AuditResult(target=directory, warnings=[f"Directory not found: {directory}"])]

        for ext in exts:
            for file_path in root.rglob(f"*{ext}"):
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if "node_modules" in str(file_path) or "__pycache__" in str(file_path):
                    continue
                if file_path.stat().st_size > 1_000_000:
                    continue

                results.append(self.audit_file(str(file_path)))

        return results

    def check_dependencies(self, requirements_file: str) -> AuditResult:
        """Check dependencies for known vulnerabilities."""
        p = Path(requirements_file)
        if not p.exists():
            return AuditResult(
                target=requirements_file,
                warnings=[f"File not found: {requirements_file}"],
            )

        result = AuditResult(target=requirements_file)
        content = p.read_text()

        known_vulnerable = {
            "django": {"<4.2": "CVE-2024-24680", "<3.2.24": "CVE-2024-27351"},
            "flask": {"<2.3.2": "CVE-2023-30861"},
            "requests": {"<2.31.0": "CVE-2023-32681"},
            "cryptography": {"<41.0.0": "Multiple CVEs"},
            "pillow": {"<10.0.0": "Multiple CVEs"},
            "urllib3": {"<1.26.17": "CVE-2023-43804"},
        }

        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            for pkg, versions in known_vulnerable.items():
                if pkg in line.lower():
                    for version_range, cve in versions.items():
                        result.info.append(
                            f"Checking {pkg}: {line} — known vulnerabilities exist for {version_range}"
                        )

        if not result.info:
            result.info.append("No known vulnerable packages detected in basic check.")

        return result

    def check_secrets_in_code(self, code: str, file_path: str = "<string>") -> AuditResult:
        """Scan for hardcoded secrets and API keys."""
        result = AuditResult(target=file_path)

        secret_patterns = [
            (r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9]{20,})["\']', "API Key"),
            (r'(?:secret|secret[_-]?key)\s*[=:]\s*["\']([A-Za-z0-9]{16,})["\']', "Secret Key"),
            (r'(?:password|passwd|pwd)\s*[=:]\s*["\'](.{8,})["\']', "Password"),
            (r'(?:token|auth[_-]?token)\s*[=:]\s*["\']([A-Za-z0-9._-]{20,})["\']', "Auth Token"),
            (r'(?:private[_-]?key)\s*[=:]\s*["\']([A-Za-z0-9+/]{40,})["\']', "Private Key"),
            (r'(?:aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\']?(AKIA[A-Z0-9]{16})["\']?', "AWS Access Key"),
            (r'(?:ghp|gho|ghu|ghs|ghr)[A-Za-z0-9]{36}', "GitHub Token"),
            (r'sk-[A-Za-z0-9]{32,}', "OpenAI API Key"),
        ]

        for i, line in enumerate(code.split("\n"), 1):
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    result.vulnerabilities.append(
                        Vulnerability(
                            severity="critical",
                            category="secrets",
                            title=f"Hardcoded {secret_type}",
                            description=f"A hardcoded {secret_type} was found in the code.",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=f"  {i}: {line.strip()[:100]}",
                            recommendation="Move to environment variable or secrets manager",
                            cwe_id="CWE-798",
                        )
                    )

        return result

    def generate_report(self, results: list[AuditResult]) -> str:
        """Generate a comprehensive security report."""
        lines = [
            "=" * 70,
            "         SECURITY AUDIT REPORT",
            "=" * 70,
            "",
        ]

        total_vulns = sum(len(r.vulnerabilities) for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 100

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for r in results:
            for sev, count in r.summary.items():
                severity_counts[sev] = severity_counts.get(sev, 0) + count

        lines.extend([
            f"Files scanned: {len(results)}",
            f"Total findings: {total_vulns}",
            f"Security score: {avg_score:.0f}/100",
            "",
            "Severity Breakdown:",
            f"  CRITICAL: {severity_counts['critical']}",
            f"  HIGH:     {severity_counts['high']}",
            f"  MEDIUM:   {severity_counts['medium']}",
            f"  LOW:      {severity_counts['low']}",
            f"  INFO:     {severity_counts['info']}",
            "",
            "-" * 70,
        ])

        for r in results:
            if r.vulnerabilities:
                lines.append(f"\nFile: {r.target} (score: {r.score:.0f}/100)")
                for v in r.vulnerabilities:
                    icon = {"critical": "!!!", "high": "!!", "medium": "!", "low": "-", "info": "i"}[v.severity]
                    lines.extend([
                        f"  [{icon}] {v.severity.upper()}: {v.title}",
                        f"      {v.description}",
                        f"      Line {v.line_number}: {v.code_snippet.strip()[:80]}",
                        f"      Fix: {v.recommendation}",
                        f"      {v.cwe_id}" if v.cwe_id else "",
                        "",
                    ])

        lines.extend([
            "=" * 70,
            "END OF REPORT",
            "=" * 70,
        ])

        return "\n".join(lines)
