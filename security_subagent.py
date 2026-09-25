"""Security Sub-Agent for Buddy.ai - Automated security checks and fixes."""
import os
import re
import ast
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityIssue:
    """Represents a security issue."""
    severity: str  # HIGH, MEDIUM, LOW
    file: str
    line: int
    issue: str
    recommendation: str
    auto_fixable: bool = False


class SecuritySubAgent:
    """Sub-agent for automated security checks and fixes."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.issues: list[SecurityIssue] = []
    
    def scan_file(self, filepath: Path) -> list[SecurityIssue]:
        """Scan a single file for security issues."""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for hardcoded secrets
                secret_patterns = [
                    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
                    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
                    (r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret key'),
                    (r'(?i)(access[_-]?token|accesstoken)\s*=\s*["\'][^"\']+["\']', 'Hardcoded access token'),
                    (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', 'Private key exposed'),
                ]
                
                for pattern, issue_msg in secret_patterns:
                    if re.search(pattern, line):
                        # Skip test files and documentation
                        if 'test' not in str(filepath).lower() and 'readme' not in str(filepath).lower():
                            issues.append(SecurityIssue(
                                severity='HIGH',
                                file=str(filepath),
                                line=i,
                                issue=issue_msg,
                                recommendation='Use environment variables or secrets manager',
                                auto_fixable=False
                            ))
                
                # Check for SQL injection
                if re.search(r'(?i)(execute|cursor\.execute)\s*\(.*%s', line):
                    issues.append(SecurityIssue(
                        severity='HIGH',
                        file=str(filepath),
                        line=i,
                        issue='Potential SQL injection',
                        recommendation='Use parameterized queries',
                        auto_fixable=False
                    ))
                
                # Check for command injection
                if re.search(r'os\.system\(', line) or re.search(r'subprocess\.call\(.*shell\s*=\s*True', line):
                    issues.append(SecurityIssue(
                        severity='HIGH',
                        file=str(filepath),
                        line=i,
                        issue='Potential command injection',
                        recommendation='Use subprocess with shell=False and list args',
                        auto_fixable=False
                    ))
                
                # Check for eval/exec
                if re.search(r'\beval\s*\(', line) or re.search(r'\bexec\s*\(', line):
                    issues.append(SecurityIssue(
                        severity='MEDIUM',
                        file=str(filepath),
                        line=i,
                        issue='Use of eval/exec',
                        recommendation='Avoid eval/exec, use safer alternatives',
                        auto_fixable=False
                    ))
                
                # Check for insecure temp files
                if 'tempfile.mktemp' in line:
                    issues.append(SecurityIssue(
                        severity='MEDIUM',
                        file=str(filepath),
                        line=i,
                        issue='Insecure temporary file',
                        recommendation='Use tempfile.NamedTemporaryFile or mkstemp',
                        auto_fixable=True
                    ))
                
                # Check for debug mode
                if re.search(r'debug\s*=\s*True', line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        severity='MEDIUM',
                        file=str(filepath),
                        line=i,
                        issue='Debug mode enabled',
                        recommendation='Disable debug mode in production',
                        auto_fixable=True
                    ))
                
                # Check for insecure HTTP
                if re.search(r'http://(?!localhost|127\.0\.0\.1)', line):
                    if 'test' not in str(filepath).lower():
                        issues.append(SecurityIssue(
                            severity='LOW',
                            file=str(filepath),
                            line=i,
                            issue='Insecure HTTP connection',
                            recommendation='Use HTTPS for external connections',
                            auto_fixable=False
                        ))
        
        except Exception as e:
            issues.append(SecurityIssue(
                severity='LOW',
                file=str(filepath),
                line=0,
                issue=f'Scan error: {str(e)}',
                recommendation='Check file permissions and encoding',
                auto_fixable=False
            ))
        
        return issues
    
    def scan_directory(self, directory: Path = None) -> list[SecurityIssue]:
        """Scan entire directory for security issues."""
        if directory is None:
            directory = self.project_root
        
        self.issues = []
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden dirs, venv, and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    file_issues = self.scan_file(filepath)
                    self.issues.extend(file_issues)
        
        return self.issues
    
    def get_summary(self) -> dict:
        """Get summary of security issues."""
        summary = {
            'total': len(self.issues),
            'high': len([i for i in self.issues if i.severity == 'HIGH']),
            'medium': len([i for i in self.issues if i.severity == 'MEDIUM']),
            'low': len([i for i in self.issues if i.severity == 'LOW']),
            'auto_fixable': len([i for i in self.issues if i.auto_fixable]),
        }
        return summary
    
    def generate_report(self) -> str:
        """Generate security report."""
        summary = self.get_summary()
        
        report = [
            '=' * 60,
            'SECURITY AUDIT REPORT',
            '=' * 60,
            f'Total Issues: {summary["total"]}',
            f'High Severity: {summary["high"]}',
            f'Medium Severity: {summary["medium"]}',
            f'Low Severity: {summary["low"]}',
            f'Auto-fixable: {summary["auto_fixable"]}',
            '',
        ]
        
        # Group by file
        by_file = {}
        for issue in self.issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        for filepath, issues in sorted(by_file.items()):
            report.append(f'\n{filepath}:')
            for issue in issues:
                report.append(f'  [{issue.severity:6}] Line {issue.line}: {issue.issue}')
                report.append(f'         Recommendation: {issue.recommendation}')
        
        report.append('')
        report.append('=' * 60)
        
        return '\n'.join(report)


def run_security_scan(project_root: str = None) -> str:
    """Run security scan and return report."""
    agent = SecuritySubAgent(project_root)
    agent.scan_directory()
    return agent.generate_report()


if __name__ == '__main__':
    print(run_security_scan())
