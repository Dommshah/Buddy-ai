"""Git version-control tools for the Kaka.ai agent."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.tools import Tool


def _git(args: list[str], cwd: str | None = None) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        out = ""
        if result.stdout:
            out += result.stdout
        if result.stderr:
            out += result.stderr
        if result.returncode != 0:
            out += f"\nExit code: {result.returncode}"
        return out.strip() or "(no output)"
    except FileNotFoundError:
        return "Error: git is not installed."
    except subprocess.TimeoutExpired:
        return "Error: git command timed out."


def _check_repo(cwd: str | None = None) -> str | None:
    probe = _git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
    if not probe.strip().endswith("true"):
        return f"Error: not a git repository ({probe[:100]})"
    return None


def _status(cwd: str | None = None) -> str:
    if err := _check_repo(cwd):
        return err
    return _git(["status", "--short", "-b"], cwd=cwd)


def _diff(cwd: str | None = None, staged: bool = False) -> str:
    if err := _check_repo(cwd):
        return err
    args = ["diff", "--stat"] if not staged else ["diff", "--cached", "--stat"]
    stat = _git(args, cwd=cwd)
    full = _git(["diff", "--cached"] if staged else ["diff"], cwd=cwd)
    if len(full) > 20_000:
        full = full[:20_000] + "\n... (diff truncated)"
    return f"{stat}\n\n{full}" if full != "(no output)" else stat


def _log(count: int = 10, cwd: str | None = None) -> str:
    if err := _check_repo(cwd):
        return err
    count = max(1, min(int(count), 50))
    return _git(
        ["log", f"-{count}", "--pretty=format:%h %ad %an%n  %s", "--date=short"],
        cwd=cwd,
    )


def _branch(branch: str = "", create: bool = False, cwd: str | None = None) -> str:
    if err := _check_repo(cwd):
        return err
    if branch and create:
        return _git(["checkout", "-b", branch], cwd=cwd)
    if branch:
        return _git(["checkout", branch], cwd=cwd)
    return _git(["branch", "-a"], cwd=cwd)


def _commit(message: str, add_all: bool = True, cwd: str | None = None) -> str:
    if err := _check_repo(cwd):
        return err
    if not message.strip():
        return "Error: commit message required."
    if add_all:
        added = _git(["add", "-A"], cwd=cwd)
        if added.startswith("Error"):
            return added
    return _git(["commit", "-m", message], cwd=cwd)


def _show(file: str, revision: str = "HEAD", cwd: str | None = None) -> str:
    if err := _check_repo(cwd):
        return err
    content = _git(["show", f"{revision}:{file}"], cwd=cwd)
    if len(content) > 30_000:
        content = content[:30_000] + "\n... (truncated)"
    return content


def register(registry: Any) -> None:
    common = {
        "type": "object",
        "properties": {
            "cwd": {"type": "string", "description": "Repository path (default: current dir)"},
        },
        "required": [],
    }
    registry.register(Tool(
        name="git_status",
        description="Show git working-tree status of a repository.",
        parameters=common,
        execute=_status,
    ))
    registry.register(Tool(
        name="git_diff",
        description="Show unstaged (or staged) changes diff summary.",
        parameters={
            "type": "object",
            "properties": {**common["properties"], "staged": {"type": "boolean", "description": "Show staged changes instead"}},
            "required": [],
        },
        execute=lambda cwd=None, staged=False: _diff(cwd, staged),
    ))
    registry.register(Tool(
        name="git_log",
        description="Show recent commit history.",
        parameters={
            "type": "object",
            "properties": {**common["properties"], "count": {"type": "integer", "description": "Number of commits (default 10)"}},
            "required": [],
        },
        execute=_log,
    ))
    registry.register(Tool(
        name="git_branch",
        description="List branches, or checkout/create one when 'branch' given.",
        parameters={
            "type": "object",
            "properties": {
                **common["properties"],
                "branch": {"type": "string", "description": "Branch name to switch to / create"},
                "create": {"type": "boolean", "description": "Create the branch if missing (default false)"},
            },
            "required": [],
        },
        execute=_branch,
    ))
    registry.register(Tool(
        name="git_commit",
        description="Stage all changes and create a commit with the given message.",
        parameters={
            "type": "object",
            "properties": {
                **common["properties"],
                "message": {"type": "string", "description": "Commit message"},
                "add_all": {"type": "boolean", "description": "Stage all changes first (default true)"},
            },
            "required": ["message"],
        },
        execute=_commit,
    ))
    registry.register(Tool(
        name="git_show",
        description="Show a file's contents at a given revision.",
        parameters={
            "type": "object",
            "properties": {
                **common["properties"],
                "file": {"type": "string", "description": "File path inside repo"},
                "revision": {"type": "string", "description": "Git revision (default HEAD)"},
            },
            "required": ["file"],
        },
        execute=_show,
    ))
