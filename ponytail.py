"""Ponytail Integration - Lazy Senior Dev Mode for Buddy.ai.

Based on https://github.com/DietrichGebert/ponytail
License: MIT

Ponytail makes AI agents write minimal, efficient code by following
the YAGNI principle and using native platform features.
"""
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class PonytailConfig:
    """Ponytail configuration."""
    mode: str = "full"  # lite, full, ultra, off
    enabled: bool = True


# Default rules text
PONYTAIL_RULES = """# Ponytail, lazy senior dev mode

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

Rules:
- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever.
- Fewest files possible. Shortest working diff wins.
- Question complex requests: "Do you actually need X, or does Y cover it?"

Not lazy about: input validation, error handling, security, accessibility.
"""


class PonytailManager:
    """Manages Ponytail lazy dev mode."""
    
    def __init__(self, config: PonytailConfig | None = None):
        self.config = config or PonytailConfig()
    
    def get_mode(self) -> str:
        """Get current mode."""
        return self.config.mode
    
    def set_mode(self, mode: str) -> str:
        """Set mode and return confirmation."""
        valid_modes = ["lite", "full", "ultra", "off"]
        if mode not in valid_modes:
            return f"Invalid mode. Choose from: {', '.join(valid_modes)}"
        
        self.config.mode = mode
        self.config.enabled = mode != "off"
        
        descriptions = {
            "lite": "Build what's asked, but name the lazier alternative in one line.",
            "full": "The ladder enforced. Stdlib and native first. Shortest diff, shortest explanation.",
            "ultra": "YAGNI extremist. Deletion before addition. Ship the one-liner.",
            "off": "Ponytail disabled. Normal mode."
        }
        
        return f"Ponytail mode: {mode} — {descriptions[mode]}"
    
    def get_rules(self) -> str:
        """Get the rules text."""
        if not self.config.enabled:
            return "Ponytail is disabled."
        return PONYTAIL_RULES
    
    def review_code(self, code: str) -> dict:
        """Review code for over-engineering."""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for unnecessary abstractions
            if re.match(r'^class\s+\w+.*:', stripped):
                if 'Interface' in stripped or 'Abstract' in stripped:
                    issues.append(f"Line {i}: Unnecessary abstraction — {stripped}")
            
            # Check for unnecessary imports
            if stripped.startswith('import ') or stripped.startswith('from '):
                if 'typing' in stripped and 'Optional' in stripped:
                    suggestions.append(f"Line {i}: Consider if Optional is really needed")
            
            # Check for boilerplate
            if 'if __name__ == "__main__":' in stripped:
                suggestions.append(f"Line {i}: Boilerplate — include only if needed for testing")
            
            # Check for complex patterns
            if 'try:' in stripped and 'except Exception:' in stripped:
                issues.append(f"Line {i}: Broad exception handling — catch specific exceptions")
        
        return {
            "mode": self.config.mode,
            "issues": issues,
            "suggestions": suggestions,
            "verdict": "REFACTOR" if issues else "OK"
        }
    
    def audit_file(self, filepath: str) -> dict:
        """Audit a file for over-engineering."""
        try:
            path = Path(filepath)
            if not path.exists():
                return {"error": f"File not found: {filepath}"}
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            result = self.review_code(content)
            result["file"] = filepath
            result["lines"] = len(content.split('\n'))
            
            return result
            
        except Exception as e:
            return {"error": str(e)}


# Global instance
_manager: Optional[PonytailManager] = None


def get_ponytail_manager() -> PonytailManager:
    """Get or create the global Ponytail manager."""
    global _manager
    if _manager is None:
        _manager = PonytailManager()
    return _manager


def set_mode(mode: str) -> str:
    """Set Ponytail mode."""
    return get_ponytail_manager().set_mode(mode)


def get_mode() -> str:
    """Get current mode."""
    return get_ponytail_manager().get_mode()


def get_rules() -> str:
    """Get the rules text."""
    return get_ponytail_manager().get_rules()


def review_code(code: str) -> dict:
    """Review code for over-engineering."""
    return get_ponytail_manager().review_code(code)


def audit_file(filepath: str) -> dict:
    """Audit a file."""
    return get_ponytail_manager().audit_file(filepath)
