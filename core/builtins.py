"""Built-in tools for the AI Agent."""
from __future__ import annotations

import glob
import os
import platform
import subprocess
import textwrap
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from .tools import Tool, ToolRegistry


def register_built_in_tools(registry: ToolRegistry) -> None:
    """Register all built-in tools."""

    # ── File Operations ──────────────────────────────────────────────
    registry.register(
        Tool(
            name="read_file",
            description="Read the contents of a file. Returns the full text content.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file"},
                },
                "required": ["path"],
            },
            execute=_read_file,
        )
    )

    registry.register(
        Tool(
            name="write_file",
            description="Write content to a file. Creates parent directories if needed.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write to"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
            execute=_write_file,
        )
    )

    registry.register(
        Tool(
            name="list_files",
            description="List files and directories at a given path.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current dir)"},
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to filter (e.g. '*.py')",
                    },
                },
            },
            execute=_list_files,
        )
    )

    registry.register(
        Tool(
            name="search_files",
            description="Search for text patterns across files using regex.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "Directory to search in (default: current dir)"},
                    "include": {"type": "string", "description": "File pattern to include (e.g. '*.py')"},
                },
                "required": ["pattern"],
            },
            execute=_search_files,
        )
    )

    # ── Shell / System ───────────────────────────────────────────────
    registry.register(
        Tool(
            name="run_command",
            description="Execute a shell command. Returns stdout and stderr.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "cwd": {"type": "string", "description": "Working directory (optional)"},
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 60)",
                    },
                },
                "required": ["command"],
            },
            execute=_run_command,
        )
    )

    registry.register(
        Tool(
            name="system_info",
            description="Get system information (OS, CPU, memory, Python version).",
            parameters={"type": "object", "properties": {}},
            execute=_system_info,
        )
    )

    # ── Web / Network ────────────────────────────────────────────────
    registry.register(
        Tool(
            name="fetch_url",
            description="Fetch content from a URL. Returns the response body.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "method": {"type": "string", "description": "HTTP method (default: GET)"},
                    "allow_private": {
                        "type": "boolean",
                        "description": "Allow localhost/private-network URLs (default: false)",
                    },
                },
                "required": ["url"],
            },
            execute=_fetch_url,
        )
    )

    # ── DateTime ─────────────────────────────────────────────────────
    registry.register(
        Tool(
            name="get_datetime",
            description="Get current date, time, and timezone information.",
            parameters={"type": "object", "properties": {}},
            execute=_get_datetime,
        )
    )

    # ── Memory ───────────────────────────────────────────────────────
    registry.register(
        Tool(
            name="save_memory",
            description="Save a key-value pair or note to persistent memory.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key/label"},
                    "value": {"type": "string", "description": "Content to remember"},
                    "category": {
                        "type": "string",
                        "description": "Category (note, preference, fact, task)",
                    },
                },
                "required": ["key", "value"],
            },
            execute=_save_memory,
        )
    )

    registry.register(
        Tool(
            name="recall_memory",
            description="Recall saved memories. Optionally filter by category.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Specific key to look up (optional)"},
                    "category": {"type": "string", "description": "Filter by category (optional)"},
                },
            },
            execute=_recall_memory,
        )
    )

    # ── Code Execution ───────────────────────────────────────────────
    registry.register(
        Tool(
            name="run_python",
            description="Execute a Python code snippet and return the output.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30)",
                    },
                },
                "required": ["code"],
            },
            execute=_run_python,
        )
    )

    # ── JSON Operations ──────────────────────────────────────────────
    registry.register(
        Tool(
            name="json_query",
            description="Query a JSON string using a dot-notation path.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "JSON string to query"},
                    "path": {
                        "type": "string",
                        "description": "Dot-notation path (e.g. 'users.0.name')",
                    },
                },
                "required": ["data", "path"],
            },
            execute=_json_query,
        )
    )

    # ── Calculator ───────────────────────────────────────────────────
    registry.register(
        Tool(
            name="calculate",
            description="Evaluate a mathematical expression.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"},
                },
                "required": ["expression"],
            },
            execute=_calculate,
        )
    )

    # ── Clipboard ────────────────────────────────────────────────────
    registry.register(
        Tool(
            name="clipboard",
            description="Read from or write to the system clipboard.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "'read' or 'write'"},
                    "text": {"type": "string", "description": "Text to write (if action is write)"},
                },
                "required": ["action"],
            },
            execute=_clipboard,
        )
    )

    # ── COGNITION TOOLS ──────────────────────────────────────────────

    registry.register(
        Tool(
            name="reason",
            description="Advanced reasoning engine. Supports chain-of-thought, tree-of-thought, deductive, inductive, abductive, analogical, and critical analysis modes.",
            parameters={
                "type": "object",
                "properties": {
                    "problem": {"type": "string", "description": "The problem or question to reason about"},
                    "mode": {
                        "type": "string",
                        "description": "Reasoning mode",
                        "enum": ["chain_of_thought", "tree_of_thought", "deductive", "inductive", "abductive", "analogical", "critical", "reflective"],
                        "default": "chain_of_thought",
                    },
                    "context": {"type": "string", "description": "Additional context (premises, evidence, or domain info)"},
                },
                "required": ["problem"],
            },
            execute=_cog_reasoning,
        )
    )

    registry.register(
        Tool(
            name="security_audit",
            description="Perform security audit on code, files, or directories. Checks for vulnerabilities, hardcoded secrets, and security issues.",
            parameters={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Code string, file path, or directory path to audit"},
                    "scan_type": {
                        "type": "string",
                        "description": "Type of scan",
                        "enum": ["code", "file", "directory", "secrets", "dependencies"],
                        "default": "file",
                    },
                },
                "required": ["target"],
            },
            execute=None,
        )
    )

    registry.register(
        Tool(
            name="content_create",
            description="Generate content: blog posts, emails, social media, landing pages, technical articles, product descriptions, press releases, reports, proposals, or video scripts.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic or subject for the content"},
                    "content_type": {
                        "type": "string",
                        "description": "Type of content to create",
                        "enum": ["blog_post", "email_sequence", "social_media", "landing_page", "technical_article", "product_description", "press_release", "report_executive", "business_proposal", "video_script"],
                        "default": "blog_post",
                    },
                },
                "required": ["topic"],
            },
            execute=_cog_reasoning,
        )
    )

    registry.register(
        Tool(
            name="code_analyze",
            description="Analyze code for complexity, issues, bugs, and maintainability. Supports Python, JavaScript, TypeScript.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to analyze"},
                    "language": {"type": "string", "description": "Programming language", "default": "python"},
                    "file_path": {"type": "string", "description": "File path for context (optional)"},
                },
                "required": ["code"],
            },
            execute=_cog_code_analyze,
        )
    )

    registry.register(
        Tool(
            name="code_generate",
            description="Generate a function and its test boilerplate from a description.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the function should do"},
                    "language": {"type": "string", "description": "Target language (python, javascript, typescript, go, rust)", "default": "python"},
                    "name": {"type": "string", "description": "Function name", "default": "my_function"},
                },
                "required": ["description"],
            },
            execute=_cog_code_generate,
        )
    )

    registry.register(
        Tool(
            name="creative_idea",
            description="Generate creative ideas using brainstorming, SCAMPER, random association, or divergent/convergent thinking.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic or problem to brainstorm"},
                    "approach": {
                        "type": "string",
                        "description": "Brainstorming approach",
                        "enum": ["divergent", "convergent", "scamper", "random_association"],
                        "default": "divergent",
                    },
                    "num_ideas": {"type": "integer", "description": "Number of ideas to generate", "default": 5},
                },
                "required": ["topic"],
            },
            execute=_cog_creative_idea,
        )
    )

    registry.register(
        Tool(
            name="creative_writing_prompt",
            description="Generate a creative writing prompt for fiction, poetry, or creative nonfiction.",
            parameters={
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre (sci-fi, fantasy, horror, romance, etc.)", "default": "any"},
                    "mood": {"type": "string", "description": "Mood (dark, whimsical, tense, hopeful, etc.)", "default": "any"},
                },
            },
            execute=_cog_creative_prompt,
        )
    )

    registry.register(
        Tool(
            name="pattern_detect",
            description="Detect patterns in text or numerical data. Identifies trends, sentiment, repetition, outliers, and correlations.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Text or JSON array of numbers to analyze"},
                    "data_type": {
                        "type": "string",
                        "description": "Type of data",
                        "enum": ["text", "numerical"],
                        "default": "text",
                    },
                },
                "required": ["data"],
            },
            execute=_cog_pattern_detect,
        )
    )

    registry.register(
        Tool(
            name="predict",
            description="Make predictions on numerical data using linear regression and moving average. Classifies trends and estimates volatility.",
            parameters={
                "type": "object",
                "properties": {
                    "values": {"type": "string", "description": "JSON array of historical values, e.g. '[1,2,3,4,5]'"},
                    "steps_ahead": {"type": "integer", "description": "How many steps to predict ahead", "default": 3},
                },
                "required": ["values"],
            },
            execute=_cog_predict,
        )
    )

    registry.register(
        Tool(
            name="verify",
            description="Verify a claim or statement. Checks logical validity, cross-references, and confidence scoring.",
            parameters={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The claim to verify"},
                    "context": {"type": "string", "description": "Supporting context or reference material"},
                },
                "required": ["claim"],
            },
            execute=_cog_verify,
        )
    )

    registry.register(
        Tool(
            name="learn_store",
            description="Store a learned pattern or knowledge for future recall.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category (pattern, knowledge, preference, rule)"},
                    "pattern": {"type": "string", "description": "The input pattern or trigger"},
                    "output": {"type": "string", "description": "The learned response or output"},
                },
                "required": ["category", "pattern", "output"],
            },
            execute=_cog_learn_store,
        )
    )

    registry.register(
        Tool(
            name="learn_recall",
            description="Recall previously learned patterns and knowledge.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query to find relevant learned patterns"},
                },
                "required": ["query"],
            },
            execute=_cog_learn_recall,
        )
    )

    registry.register(
        Tool(
            name="learn_stats",
            description="Get statistics about the agent's learning progress and skill levels.",
            parameters={"type": "object", "properties": {}},
            execute=_cog_learn_stats,
        )
    )

    registry.register(
        Tool(
            name="autonomy_plan",
            description="Create an execution plan with steps for autonomous task completion.",
            parameters={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The overall goal to achieve"},
                    "steps": {"type": "string", "description": "Newline-separated list of steps to execute"},
                },
                "required": ["goal", "steps"],
            },
            execute=_cog_autonomy_plan,
        )
    )

    registry.register(
        Tool(
            name="autonomy_decide",
            description="Make a decision between multiple options using weighted criteria.",
            parameters={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The decision question"},
                    "options": {"type": "string", "description": "Newline-separated list of options to choose from"},
                },
                "required": ["question", "options"],
            },
            execute=_cog_autonomy_decide,
        )
    )

    registry.register(
        Tool(
            name="voice_transcribe",
            description="Transcribe an audio file to text using speech recognition.",
            parameters={
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string", "description": "Path to the audio file"},
                },
                "required": ["audio_path"],
            },
            execute=_cog_voice_transcribe,
        )
    )

    registry.register(
        Tool(
            name="voice_listen",
            description="Listen from the microphone and transcribe speech to text.",
            parameters={"type": "object", "properties": {}},
            execute=_cog_voice_listen,
        )
    )

    registry.register(
        Tool(
            name="voice_speak",
            description="Convert text to speech (text-to-speech).",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to speak aloud"},
                    "output_path": {"type": "string", "description": "Optional file path to save audio"},
                },
                "required": ["text"],
            },
            execute=_cog_voice_speak,
        )
    )

    registry.register(
        Tool(
            name="data_analyze",
            description="Analyze structured data (JSON array of objects or numbers). Provides statistics, patterns, and column-level insights.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "JSON array to analyze"},
                },
                "required": ["data"],
            },
            execute=_cog_data_analyze,
        )
    )

    # ── AGENT & RESEARCH TOOLS ───────────────────────────────────────

    registry.register(
        Tool(
            name="agent_spawn",
            description="Spawn a sub-agent with a specific role for parallel task execution.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name"},
                    "role": {
                        "type": "string",
                        "description": "Agent role",
                        "enum": ["researcher", "coder", "analyzer", "writer", "reviewer", "coordinator", "custom"],
                        "default": "custom",
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tool capabilities",
                    },
                },
                "required": ["name"],
            },
            execute=_cog_agent_spawn,
        )
    )

    registry.register(
        Tool(
            name="agent_status",
            description="Get status of all sub-agents or a specific agent.",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Specific agent ID (optional)"},
                },
            },
            execute=_cog_agent_status,
        )
    )

    registry.register(
        Tool(
            name="agent_delegate",
            description="Delegate a task to a specific sub-agent.",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Target agent ID"},
                    "task": {"type": "string", "description": "Task description"},
                },
                "required": ["agent_id", "task"],
            },
            execute=_cog_agent_delegate,
        )
    )

    registry.register(
        Tool(
            name="deep_research",
            description="Perform deep multi-source research on a topic. Returns structured findings with citations.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Research query or topic"},
                    "depth": {
                        "type": "integer",
                        "description": "Research depth (1=quick, 2=standard, 3=deep, 5=exhaustive)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
            execute=_cog_deep_research,
        )
    )

    registry.register(
        Tool(
            name="browse_page",
            description="Fetch and extract content from a specific URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to browse"},
                },
                "required": ["url"],
            },
            execute=_cog_browse_page,
        )
    )

    registry.register(
        Tool(
            name="fact_check",
            description="Fact-check a claim against web sources.",
            parameters={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "Claim to verify"},
                },
                "required": ["claim"],
            },
            execute=_cog_fact_check,
        )
    )

    registry.register(
        Tool(
            name="research_report",
            description="Generate a comprehensive research report on a topic.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Research topic"},
                    "depth": {"type": "integer", "description": "Research depth (1-5)", "default": 3},
                },
                "required": ["topic"],
            },
            execute=_cog_research_report,
        )
    )

    registry.register(
        Tool(
            name="knowledge_store",
            description="Store a knowledge entry in the persistent knowledge base.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Knowledge topic"},
                    "category": {"type": "string", "description": "Category (programming, security, architecture, etc.)"},
                    "content": {"type": "string", "description": "Knowledge content"},
                    "source": {"type": "string", "description": "Source of knowledge", "default": "agent"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for indexing",
                    },
                },
                "required": ["topic", "category", "content"],
            },
            execute=_cog_knowledge_store,
        )
    )

    registry.register(
        Tool(
            name="knowledge_query",
            description="Query the knowledge base for relevant information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "category": {"type": "string", "description": "Filter by category (optional)"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["query"],
            },
            execute=_cog_knowledge_query,
        )
    )

    registry.register(
        Tool(
            name="autonomous_think",
            description="Run autonomous reasoning loop — observe, analyze, hypothesize, decide, reflect.",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Problem or question to think about"},
                },
                "required": ["input"],
            },
            execute=_cog_autonomous_think,
        )
    )

    registry.register(
        Tool(
            name="compare_sources",
            description="Compare information across multiple web sources.",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to compare",
                    },
                },
                "required": ["urls"],
            },
            execute=_cog_compare_sources,
        )
    )

    registry.register(
        Tool(
            name="platform_info",
            description="Get platform compatibility information.",
            parameters={"type": "object", "properties": {}},
            execute=_cog_platform_info,
        )
    )

    # ── Security Sub-Agent ────────────────────────────────────────────
    registry.register(
        Tool(
            name="security_scan",
            description="Run security audit on codebase. Scans for vulnerabilities, hardcoded secrets, and security issues.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to scan (default: current dir)"},
                },
            },
            execute=_cog_security_scan,
        )
    )

    # ── Extended tool plugins ────────────────────────────────────────
    # Loaded LAST so they can override built-ins; a missing dependency
    # skips one plugin without breaking the rest of the agent.
    import logging as _logging

    for module_name in ("plugins.git_tools", "plugins.sql_tool", "plugins.memory_rag", "plugins.vision_tools", "plugins.hf_tools", "plugins.doc_tools"):
        try:
            import importlib

            module = importlib.import_module(module_name)
            module.register(registry)
        except Exception as e:
            _logging.warning(f"Optional plugin '{module_name}' unavailable: {e}")


# ── Tool Implementations ────────────────────────────────────────────


def _read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found: {p}"
    if not p.is_file():
        return f"Error: Not a file: {p}"
    if p.stat().st_size > _MAX_FILE_CHARS:
        content = p.read_text(encoding="utf-8", errors="replace")[: _MAX_FILE_CHARS]
        truncated = True
    else:
        content = p.read_text(encoding="utf-8", errors="replace")
        truncated = False
    lines = content.split("\n")
    numbered = "\n".join(f"{i + 1:4}: {line}" for i, line in enumerate(lines))
    note = f"\n... (file larger than {_MAX_FILE_CHARS} chars — truncated)" if truncated else ""
    return f"File: {p} ({p.stat().st_size} bytes, {len(lines)} lines){note}\n\n{numbered}"


def _write_file(path: str, content: str) -> str:
    if len(content or "") > _MAX_FILE_WRITE:
        return f"Error: content too large ({len(content)} chars, max {_MAX_FILE_WRITE})."
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {p}"


def _list_files(path: str = ".", pattern: str | None = None) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        return f"Error: Not a directory: {p}"

    if pattern:
        entries = sorted(p.glob(pattern))
    else:
        entries = sorted(p.iterdir())

    lines = []
    for entry in entries[:100]:
        prefix = "📁" if entry.is_dir() else "📄"
        size = f" ({entry.stat().st_size:,} bytes)" if entry.is_file() else ""
        lines.append(f"  {prefix} {entry.name}{size}")

    if len(entries) > 100:
        lines.append(f"  ... and {len(entries) - 100} more")

    return f"Contents of {p}:\n" + "\n".join(lines) if lines else f"Empty directory: {p}"


def _search_files(pattern: str, path: str = ".", include: str | None = None) -> str:
    import re

    for candidate in (pattern, include):
        if not candidate:
            continue
        parts = Path(candidate).parts
        if candidate.startswith(("/", "~")) or ".." in parts:
            return "Error: search patterns may not be absolute or contain '..'."

    regex = re.compile(pattern)
    root = Path(path).expanduser().resolve()
    matches: list[str] = []

    file_pattern = include or "**/*"
    for p in root.glob(file_pattern):
        if p.is_file() and p.stat().st_size < 1_000_000:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.split("\n"), 1):
                    if regex.search(line):
                        matches.append(f"{p}:{i}: {line.strip()[:120]}")
            except Exception:
                continue
        if len(matches) >= 50:
            break

    return "\n".join(matches) if matches else "No matches found."


_CATASTROPHIC_COMMAND_PATTERNS = [
    r"rm\s+(-[a-zA-Z]*[rRf][a-zA-Z]*\s+)*(/|~|\$HOME)(\s|$)",
    r"\bmkfs(\.\w+)?\b",
    r"\bdd\b[^\n|;&]*of=/dev/(sd|nvme|hd|vd)",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # fork bomb
    r"\b(shutdown|reboot|halt|poweroff)\b",
    r">\s*/dev/(sd|nvme|hd)[a-z]",
    r"chmod\s+(-R\s+)?777\s+/(\s|$)",
]

_MAX_COMMAND_OUTPUT = 50_000
_MAX_FILE_CHARS = 1_000_000
_MAX_FILE_WRITE = 2_000_000
_MAX_FETCH_BYTES = 200_000


def _run_command(command: str, cwd: str | None = None, timeout: int = 60) -> str:
    import re as _re

    for pat in _CATASTROPHIC_COMMAND_PATTERNS:
        if _re.search(pat, command):
            return (
                "BLOCKED: command matches a destructive pattern "
                f"(rule: {pat}). If the user truly intends this, they must run it manually."
            )
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        output = ""
        stdout, stderr = result.stdout or "", result.stderr or ""
        if len(stdout) > _MAX_COMMAND_OUTPUT:
            stdout = stdout[:_MAX_COMMAND_OUTPUT] + f"\n... (stdout truncated at {_MAX_COMMAND_OUTPUT} chars)"
        if len(stderr) > _MAX_COMMAND_OUTPUT:
            stderr = stderr[:_MAX_COMMAND_OUTPUT] + f"\n... (stderr truncated at {_MAX_COMMAND_OUTPUT} chars)"
        if stdout:
            output += f"STDOUT:\n{stdout}\n"
        if stderr:
            output += f"STDERR:\n{stderr}\n"
        output += f"Exit code: {result.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error: {e}"


def _system_info() -> str:
    import platform
    info = {
        "System": platform.system(),
        "Release": platform.release(),
        "Machine": platform.machine(),
        "Processor": platform.processor() or "N/A",
        "Python": platform.python_version(),
        "Current Dir": os.getcwd(),
    }
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        info["Disk Total"] = f"{total // (1024**3)} GB"
        info["Disk Free"] = f"{free // (1024**3)} GB"
    except Exception:
        pass
    return "\n".join(f"{k}: {v}" for k, v in info.items())


def _validate_public_url(url: str, allow_private: bool = False) -> str | None:
    """Return an error message if the URL must not be fetched, else None.

    Blocks non-http(s) schemes (file://, ftp://) and hosts that resolve to
    loopback/private/link-local/reserved addresses unless explicitly allowed.
    """
    import ipaddress
    import socket
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
    except Exception:
        return "Invalid URL."
    if parsed.scheme not in ("http", "https"):
        return f"Scheme '{parsed.scheme or 'none'}' not allowed — only http/https."
    host = parsed.hostname
    if not host:
        return "URL has no hostname."
    if allow_private:
        return None
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".home.arpa")):
        return f"'{host}' is a private address — pass allow_private=true to override."
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return f"Cannot resolve host: {host}"
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return f"Host '{host}' resolves to private/reserved address ({ip}) — blocked. Pass allow_private=true to override."
    return None


def _fetch_url(url: str, method: str = "GET", allow_private: bool = False) -> str:
    import json
    import httpx

    method = method.upper()
    if method not in {"GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"}:
        return f"Error: HTTP method '{method}' not allowed."

    guard = _validate_public_url(url, allow_private=allow_private)
    if guard:
        return f"Blocked: {guard}"

    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            current = url
            for hop in range(6):
                with client.stream(method, current) as resp:
                    if resp.is_redirect:
                        loc = resp.headers.get("location")
                        if not loc:
                            return f"Status: {resp.status_code} (redirect with no Location)"
                        new_url = str(httpx.URL(current).join(loc))
                        guard = _validate_public_url(new_url, allow_private=allow_private)
                        if guard and not allow_private:
                            return f"Blocked redirect ({resp.status_code}) to {new_url}: {guard}"
                        current = new_url
                        continue
                    chunks = []
                    total = 0
                    for chunk in resp.iter_bytes():
                        total += len(chunk)
                        if total > _MAX_FETCH_BYTES:
                            chunks.append(b"...<body truncated>")
                            break
                        chunks.append(chunk)
                    body = b"".join(chunks).decode("utf-8", errors="replace")
                    content_type = resp.headers.get("content-type", "")
                    if "json" in content_type:
                        try:
                            data = json.loads(body)
                            s = json.dumps(data, ensure_ascii=False)[:10000]
                            if total > _MAX_FETCH_BYTES or len(json.dumps(data, ensure_ascii=False)) > 10000:
                                s += "\n... (truncated)"
                            return f"Status: {resp.status_code}\nContent-Type: {content_type}\n\n{s}"
                        except json.JSONDecodeError:
                            pass
                    if total > _MAX_FETCH_BYTES:
                        body += f"\n\n... (body > {_MAX_FETCH_BYTES} bytes — truncated)"
                    return f"Status: {resp.status_code}\nContent-Type: {content_type}\n\n{body[:10000]}"
            return "Error: too many redirects."
    except Exception as e:
        return f"Error fetching URL: {e}"


def _get_datetime() -> str:
    now = datetime.now()
    return (
        f"Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
        f"Timestamp: {now.isoformat()}"
    )


def _memory_passphrase() -> str | None:
    """Encryption passphrase when encryption-at-rest is enabled."""
    from core.config import Config

    cfg = Config.from_env()
    return cfg.data_passphrase if getattr(cfg, "encrypt_data", False) else None


def _save_memory(key: str, value: str, category: str = "note") -> str:
    import json

    from .crypto import read_maybe_encrypted, write_sealed

    memory_dir = Path("./data/memory")
    memory_dir.mkdir(parents=True, exist_ok=True)
    mem_file = memory_dir / "memories.json"
    passphrase = _memory_passphrase()

    memories: dict[str, Any] = {}
    if mem_file.exists():
        try:
            memories = json.loads(read_maybe_encrypted(mem_file, passphrase))
        except ValueError as e:
            return f"Error: {e}"

    memories[key] = {"value": value, "category": category, "updated": datetime.now().isoformat()}
    write_sealed(mem_file, json.dumps(memories, indent=2), passphrase)
    return f"Saved to memory: '{key}' (category: {category})"


def _recall_memory(key: str | None = None, category: str | None = None) -> str:
    import json

    from .crypto import read_maybe_encrypted

    mem_file = Path("./data/memory/memories.json")
    if not mem_file.exists():
        return "No memories stored yet."

    try:
        memories = json.loads(read_maybe_encrypted(mem_file, _memory_passphrase()))
    except ValueError as e:
        return f"Error: {e}"

    if key:
        if key in memories:
            return f"{key}: {json.dumps(memories[key], indent=2)}"
        return f"No memory found for key: '{key}'"

    if category:
        filtered = {k: v for k, v in memories.items() if v.get("category") == category}
        if filtered:
            return json.dumps(filtered, indent=2)
        return f"No memories in category: '{category}'"

    return json.dumps(memories, indent=2)


def _run_python(code: str, timeout: int = 30) -> str:
    """Execute Python code in an isolated subprocess with enforced timeout."""
    import subprocess
    import sys
    import tempfile

    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=max(1, int(timeout)),
            )
        except subprocess.TimeoutExpired as te:
            partial_out = ""
            if te.stdout:
                partial_out += te.stdout.decode(errors="replace") if isinstance(te.stdout, bytes) else te.stdout
            if te.stderr:
                partial_out += te.stderr.decode(errors="replace") if isinstance(te.stderr, bytes) else te.stderr
            return (
                f"Error: execution timed out after {timeout}s and was terminated."
                + (f"\nPartial output:\n{partial_out[:2000]}" if partial_out else "")
            )
        finally:
            with suppress(OSError):
                os.unlink(tmp_path)

        output = ""
        stdout, stderr = (result.stdout or ""), (result.stderr or "")
        if len(stdout) > _MAX_COMMAND_OUTPUT:
            stdout = stdout[:_MAX_COMMAND_OUTPUT] + f"\n... (stdout truncated at {_MAX_COMMAND_OUTPUT} chars)"
        if len(stderr) > _MAX_COMMAND_OUTPUT:
            stderr = stderr[:_MAX_COMMAND_OUTPUT] + f"\n... (stderr truncated at {_MAX_COMMAND_OUTPUT} chars)"
        if stdout:
            output += f"STDOUT:\n{stdout}\n"
        if stderr:
            output += f"STDERR:\n{stderr}\n"
        output += f"Exit code: {result.returncode}"
        return output
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def _json_query(data: str, path: str) -> str:
    import json

    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    parts = path.split(".")
    current = obj
    for part in parts:
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return f"Invalid index: {part}"
        elif isinstance(current, dict):
            if part not in current:
                return f"Key not found: {part}"
            current = current[part]
        else:
            return f"Cannot traverse: {type(current)}"

    return json.dumps(current, indent=2) if not isinstance(current, str) else current


def _calculate(expression: str) -> str:
    import ast
    import math
    import operator

    safe_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    safe_funcs = {
        "sqrt": math.sqrt,
        "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "fact": math.factorial,
        "gcd": math.gcd,
        "hypot": math.hypot,
    }
    safe_consts = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf}

    def _eval(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in safe_ops:
            return safe_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in safe_ops:
            return safe_ops[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Name) and node.id in safe_consts:
            return safe_consts[node.id]
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in safe_funcs
            and not node.keywords
        ):
            args = [_eval(a) for a in node.args]
            return safe_funcs[node.func.id](*args)
        raise ValueError(f"Unsupported expression")

    try:
        # Calculator convention: treat '^' as exponentiation with correct
        # precedence by normalizing to '**' before parsing.
        expression = expression.replace("^", "**")
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error evaluating expression: {e}"


def _clipboard(action: str, text: str | None = None) -> str:
    system = platform.system()
    if action == "read":
        try:
            if system == "Linux":
                result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True)
                return result.stdout or "(clipboard is empty)"
            elif system == "Darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                return result.stdout or "(clipboard is empty)"
            else:
                return "Clipboard read not supported on this platform."
        except FileNotFoundError:
            return "Clipboard tool not found (install xclip on Linux)."
    elif action == "write" and text is not None:
        try:
            if system == "Linux":
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(text.encode())
                return "Copied to clipboard."
            elif system == "Darwin":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                proc.communicate(text.encode())
                return "Copied to clipboard."
            else:
                return "Clipboard write not supported on this platform."
        except FileNotFoundError:
            return "Clipboard tool not found (install xclip on Linux)."
    return "Invalid clipboard action. Use 'read' or 'write'."


# ── COGNITION TOOLS ──────────────────────────────────────────────────


def _cog_reasoning(problem: str, mode: str = "chain_of_thought", context: str = "") -> str:
    from cognition.reasoning.engine import ReasoningEngine, ReasoningMode, format_reasoning
    engine = ReasoningEngine()
    mode_enum = {
        "chain_of_thought": ReasoningMode.CHAIN_OF_THOUGHT,
        "tree_of_thought": ReasoningMode.TREE_OF_THOUGHT,
        "deductive": ReasoningMode.DEDUCTIVE,
        "inductive": ReasoningMode.INDUCTIVE,
        "abductive": ReasoningMode.ABDUCTIVE,
        "analogical": ReasoningMode.ANALOGICAL,
        "critical": ReasoningMode.CRITICAL,
        "reflective": ReasoningMode.REFLECTIVE,
    }.get(mode, ReasoningMode.CHAIN_OF_THOUGHT)

    if mode_enum == ReasoningMode.CHAIN_OF_THOUGHT:
        result = engine.chain_of_thought(problem, context)
    elif mode_enum == ReasoningMode.TREE_OF_THOUGHT:
        result = engine.tree_of_thought(problem, context)
    elif mode_enum == ReasoningMode.DEDUCTIVE:
        premises = [p.strip() for p in problem.split("\n") if p.strip()]
        result = engine.deductive_reasoning(premises, context or "Conclusion based on premises")
    elif mode_enum == ReasoningMode.INDUCTIVE:
        observations = [o.strip() for o in problem.split("\n") if o.strip()]
        result = engine.inductive_reasoning(observations, context or "Generalized pattern")
    elif mode_enum == ReasoningMode.ABDUCTIVE:
        explanations = [e.strip() for e in context.split("\n") if e.strip()] if context else ["Explanation A", "Explanation B"]
        result = engine.abductive_reasoning(problem, explanations)
    creator = ContentCreator()
    variables = {"topic": topic, "audience": "general", "tone": "professional", "word_count": "1500",
                 "sections": "5", "keywords": topic, "product": topic, "purpose": topic,
                 "num_emails": "5", "product_service": topic, "benefit": topic, "price": "varies",
                 "level": "intermediate", "language": "python", "platform": "blog",
                 "num_posts": "3", "news": topic, "company": "Company", "date": "today",
                 "location": "Global", "organization": "Organization", "period": "Q1 2026",
                 "project": topic, "client": "Client", "budget": "TBD", "timeline": "3 months",
                 "duration": "10 minutes", "style": "educational"}
    variables.update(kwargs)
    result = creator.generate_prompt(content_type, **variables)
    if "error" in result:
        return f"Error: {result['error']}"
    return result.get("prompt", "No prompt generated.")


def _cog_code_analyze(code: str, language: str = "python", file_path: str = "<string>") -> str:
    from cognition.code_analysis import CodeAnalyzer
    analyzer = CodeAnalyzer()
    result = analyzer.analyze(code, file_path, language)
    lines = [
        f"Code Analysis: {result.file_path} ({result.language})",
        f"Lines of code: {result.lines_of_code}",
        f"Cyclomatic complexity: {result.complexity}",
        f"Maintainability index: {result.maintainability_index:.1f}/100",
        f"Functions: {len(result.functions)}",
        f"Classes: {len(result.classes)}",
        f"Issues found: {len(result.issues)}\n",
    ]
    for issue in result.issues:
        lines.append(f"  [{issue.severity.upper()}] L{issue.line}: {issue.message}")
        lines.append(f"    Fix: {issue.suggestion}")
    return "\n".join(lines)


def _cog_code_generate(description: str, language: str = "python", name: str = "my_function") -> str:
    from cognition.code_analysis import CodeGenerator
    gen = CodeGenerator()
    result = gen.generate_function(description, language, name)
    test = gen.generate_test(name, language)
    return f"=== Function ({result['language']}) ===\n{result['code']}\n\n=== Test ===\n{test['code']}"


def _cog_creative_idea(topic: str, approach: str = "divergent", num_ideas: int = 5) -> str:
    from cognition.creativity import CreativityEngine
    engine = CreativityEngine()
    ideas = engine.brainstorm(topic, num_ideas, approach)
    lines = [f"=== Creative Ideas for: {topic} (approach: {approach}) ===\n"]
    for i, idea in enumerate(ideas, 1):
        lines.append(f"{i}. {idea.title}")
        lines.append(f"   {idea.description}")
        lines.append(f"   Score: {idea.score:.2f} (F:{idea.feasibility:.1f} I:{idea.impact:.1f} N:{idea.novelty:.1f})")
        lines.append("")
    return "\n".join(lines)


def _cog_creative_prompt(genre: str = "any", mood: str = "any") -> str:
    from cognition.creativity import CreativityEngine
    return CreativityEngine().creative_writing_prompt(genre, mood)


def _cog_pattern_detect(data: str, data_type: str = "text") -> str:
    from cognition.patterns import PatternRecognizer
    recognizer = PatternRecognizer()
    if data_type == "text":
        patterns = recognizer.detect_text_patterns(data)
    elif data_type == "numerical":
        try:
            import json
            values = json.loads(data)
            patterns = recognizer.detect_data_patterns([float(v) for v in values])
        except Exception as e:
            return f"Error parsing numerical data: {e}"
    else:
        return f"Unknown data type: {data_type}"

    if not patterns:
        return "No significant patterns detected."
    lines = [f"=== Detected Patterns ({data_type}) ===\n"]
    for p in patterns:
        lines.append(f"  [{p.pattern_type}] {p.description} (confidence: {p.confidence:.0%})")
    return "\n".join(lines)


def _cog_predict(values: str, steps_ahead: int = 3) -> str:
    from cognition.patterns import PredictionEngine
    import json
    engine = PredictionEngine()
    try:
        nums = json.loads(values)
        nums = [float(v) for v in nums]
    except Exception as e:
        return f"Error parsing data: {e}"

    linear = engine.linear_predict(nums, steps_ahead)
    ma = engine.moving_average_predict(nums, steps_ahead)
    trend = engine.classify_trend(nums)
    volatility = engine.estimate_volatility(nums)

    lines = [
        f"=== Prediction Results ===",
        f"Data points: {len(nums)}",
        f"Trend: {trend}",
        f"Volatility: {volatility:.4f}\n",
        f"Linear prediction (step +{steps_ahead}): {linear.predicted_value} (confidence: {linear.confidence:.0%})",
        f"Moving average prediction: {ma.predicted_value} (confidence: {ma.confidence:.0%})",
        f"\nSupporting patterns:",
    ]
    for p in linear.supporting_patterns:
        lines.append(f"  • {p}")
    return "\n".join(lines)


def _cog_verify(claim: str, context: str = "") -> str:
    from cognition.verification import VerificationEngine
    engine = VerificationEngine()
    result = engine.verify_claim(claim, context)
    lines = [
        f"=== Verification Result ===",
        f"Claim: {result.claim}",
        f"Verified: {'YES' if result.is_verified else 'NO'}",
        f"Confidence: {result.confidence:.0%}",
        f"Method: {result.method}",
    ]
    if result.evidence:
        lines.append(f"Evidence:")
        for e in result.evidence:
            lines.append(f"  + {e}")
    if result.notes:
        lines.append(f"Notes:")
        for n in result.notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)


def _cog_learn_store(category: str, pattern: str, output: str) -> str:
    from cognition.learning.adaptive import LearningSystem
    system = LearningSystem()
    pid = system.store_pattern(category, pattern, output)
    return f"Pattern stored with ID: {pid}"


def _cog_learn_recall(query: str) -> str:
    from cognition.learning.adaptive import LearningSystem
    system = LearningSystem()
    patterns = system.find_similar_patterns(query)
    if not patterns:
        return "No similar patterns found."
    lines = [f"=== Similar Patterns for: {query} ===\n"]
    for p in patterns:
        lines.append(f"  [{p.category}] {p.input_pattern[:60]}")
        lines.append(f"    Output: {p.learned_output[:80]}")
        lines.append(f"    Confidence: {p.confidence:.0%}, Used: {p.times_used} times")
    return "\n".join(lines)


def _cog_learn_stats() -> str:
    from cognition.learning.adaptive import LearningSystem
    import json
    system = LearningSystem()
    stats = system.get_learning_stats()
    return json.dumps(stats, indent=2, default=str)


def _cog_autonomy_plan(goal: str, steps: str) -> str:
    from cognition.autonomy import AutonomyController
    import json
    controller = AutonomyController()
    step_list = [s.strip() for s in steps.split("\n") if s.strip()]
    plan_id = controller.create_plan(goal, step_list)
    return json.dumps({"plan_id": plan_id, "tasks": len(step_list), "goal": goal}, indent=2)


def _cog_autonomy_decide(question: str, options: str) -> str:
    from cognition.autonomy import AutonomyController
    import json
    controller = AutonomyController()
    option_list = [o.strip() for o in options.split("\n") if o.strip()]
    result = controller.decide(question, option_list)
    return json.dumps(result, indent=2)


def _cog_voice_transcribe(audio_path: str) -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.transcribe_audio(audio_path)
    if result.get("success"):
        return f"Transcribed ({result.get('engine', 'unknown')}): {result['text']}"
    return f"Transcription failed: {result.get('error', 'Unknown error')}"


def _cog_voice_listen() -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.listen_from_microphone()
    if result.get("success"):
        return f" Heard ({result.get('engine', 'unknown')}): {result['text']}"
    return f"Listening failed: {result.get('error', 'Unknown error')}"


def _cog_data_analyze(data: str) -> str:
    """Analyze a JSON array of objects or numerical data."""
    import json
    from cognition.patterns import PatternRecognizer
    recognizer = PatternRecognizer()

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    if isinstance(parsed, list):
        if parsed and isinstance(parsed[0], (int, float)):
            patterns = recognizer.detect_data_patterns([float(v) for v in parsed])
            lines = [f"Numerical data analysis ({len(parsed)} values):\n"]
            for p in patterns:
                lines.append(f"  [{p.pattern_type}] {p.description} ({p.confidence:.0%})")

            mean = sum(parsed) / len(parsed)
            lines.append(f"\n  Mean: {mean:.4f}")
            lines.append(f"  Min: {min(parsed)}")
            lines.append(f"  Max: {max(parsed)}")
            return "\n".join(lines)

        elif parsed and isinstance(parsed[0], dict):
            all_keys = set()
            for row in parsed:
                all_keys.update(row.keys())
            lines = [f"Data analysis ({len(parsed)} records, {len(all_keys)} columns):\n"]
            lines.append(f"  Columns: {', '.join(sorted(all_keys))}")

            for key in sorted(all_keys):
                values = [row.get(key) for row in parsed if key in row]
                non_null = [v for v in values if v is not None and v != ""]
                lines.append(f"\n  {key}:")
                lines.append(f"    Non-null: {len(non_null)}/{len(values)}")
                lines.append(f"    Unique: {len(set(str(v) for v in non_null))}")
                try:
                    nums = [float(v) for v in non_null]
                    lines.append(f"    Numeric: min={min(nums):.2f}, max={max(nums):.2f}, avg={sum(nums)/len(nums):.2f}")
                except (ValueError, TypeError):
                    from collections import Counter
                    top = Counter(str(v) for v in non_null).most_common(3)
                    if top:
                        lines.append(f"    Top values: {', '.join(f'{v}({c})' for v, c in top)}")
            return "\n".join(lines)

    return f"Data type: {type(parsed).__name__}, unable to analyze deeply."


def _cog_voice_speak(text: str, output_path: str = "") -> str:
    """Convert text to speech. Returns confirmation when done."""
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.speak(text, output_path or None)
    if result.get("success"):
        return f"DONE_SPEAKING: Text spoken successfully. Do NOT call voice_speak again."
    return f"TTS_ERROR: {result.get('error', 'Unknown error')}"


# ── AGENT & RESEARCH TOOLS ──────────────────────────────────────────

_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from agents.orchestrator import AgentOrchestrator
        _orchestrator = AgentOrchestrator(max_agents=5)
    return _orchestrator


def _cog_agent_spawn(name: str, role: str = "custom", capabilities: list[str] | None = None) -> str:
    from agents.orchestrator import AgentRole
    orch = _get_orchestrator()
    role_enum = {
        "researcher": AgentRole.RESEARCHER,
        "coder": AgentRole.CODER,
        "analyzer": AgentRole.ANALYZER,
        "writer": AgentRole.WRITER,
        "reviewer": AgentRole.REVIEWER,
        "coordinator": AgentRole.COORDINATOR,
        "custom": AgentRole.CUSTOM,
    }.get(role, AgentRole.CUSTOM)

    try:
        agent = orch.spawn_agent(name, role_enum, capabilities or [])
        return f"Agent spawned: {agent.name} (ID: {agent.id}, Role: {agent.role.value})"
    except RuntimeError as e:
        return f"Error: {e}"


def _cog_agent_status(agent_id: str = "") -> str:
    import json
    orch = _get_orchestrator()
    if agent_id:
        agent = orch.get_agent(agent_id)
        if agent:
            return json.dumps(agent.get_status(), indent=2)
        return f"Agent not found: {agent_id}"
    return orch.get_results_summary()


def _cog_agent_delegate(agent_id: str, task: str) -> str:
    orch = _get_orchestrator()
    task_obj = orch.delegate_task(agent_id, task)
    if task_obj:
        return f"Task delegated: {task_obj.id} to agent {agent_id}"
    return f"Agent not found: {agent_id}"


def _cog_deep_research(query: str, depth: int = 3) -> str:
    from research.engine import ResearchEngine
    engine = ResearchEngine()
    result = engine.deep_research(query) if depth >= 3 else engine.standard_research(query)
    lines = [
        f"=== Deep Research: {query} ===",
        f"Sources analyzed: {len(result.sources)}",
        f"Total words: {result.total_words:,}",
        f"Confidence: {result.confidence:.0%}\n",
        f"Summary:\n{result.summary}\n",
    ]
    if result.key_findings:
        lines.append("Key Findings:")
        for i, f in enumerate(result.key_findings[:5], 1):
            lines.append(f"  {i}. {f[:150]}")
    if result.citations:
        lines.append("\nCitations:")
        for c in result.citations[:5]:
            lines.append(f"  - {c.get('title', 'N/A')}: {c.get('url', '')}")
    return "\n".join(lines)


def _cog_browse_page(url: str) -> str:
    from research.browser import EnhancedBrowser
    browser = EnhancedBrowser()
    page = browser.fetch_page(url)
    content = page.content[:5000] if page.content else "No content extracted"
    return (
        f"=== {page.title or 'Untitled'} ===\n"
        f"URL: {page.url}\n"
        f"Status: {page.status_code}\n"
        f"Words: {page.word_count}\n"
        f"Links: {len(page.links)}\n\n"
        f"{content}"
    )


def _cog_fact_check(claim: str) -> str:
    from research.engine import ResearchEngine
    import json
    engine = ResearchEngine()
    result = engine.fact_check(claim)
    lines = [
        f"=== Fact Check ===",
        f"Claim: {result['claim']}",
        f"Verdict: {result['verdict']}",
        f"Confidence: {result['confidence']:.0%}",
        f"Sources: {result['total_sources']} checked",
        f"  Supporting: {result['supporting_sources']}",
        f"  Contradicting: {result['contradicting_sources']}",
        f"  Neutral: {result['neutral_sources']}",
    ]
    return "\n".join(lines)


def _cog_research_report(topic: str, depth: int = 3) -> str:
    from research.engine import ResearchEngine
    engine = ResearchEngine()
    report = engine.generate_report(topic, depth=depth)
    lines = [
        f"=== RESEARCH REPORT: {topic} ===",
        f"Generated: {report.generated_at}",
        f"Confidence: {report.confidence_score:.0%}",
        f"Word count: {report.word_count:,}\n",
        f"--- Executive Summary ---\n{report.executive_summary}\n",
        f"--- Key Insights ---",
    ]
    for i, insight in enumerate(report.key_insights[:5], 1):
        lines.append(f"  {i}. {insight}")
    lines.append(f"\n--- Methodology ---\n{report.methodology}")
    lines.append(f"\n--- Sources ({len(report.sources)}) ---")
    for s in report.sources[:5]:
        lines.append(f"  - {s.get('title', 'N/A')}")
    return "\n".join(lines)


def _cog_knowledge_store(topic: str, category: str, content: str, source: str = "agent", tags: list[str] | None = None) -> str:
    from knowledge.base import KnowledgeBase
    kb = KnowledgeBase()
    entry_id = kb.add_entry(topic, category, content, source, 0.85, tags or [])
    return f"Knowledge stored: {entry_id} ({topic})"


def _cog_knowledge_query(query: str, category: str | None = None, limit: int = 5) -> str:
    from knowledge.base import KnowledgeBase
    kb = KnowledgeBase()
    results = kb.query(query, category, limit)
    if not results:
        return f"No knowledge found for: {query}"
    lines = [f"=== Knowledge Results for: {query} ===\n"]
    for entry in results:
        lines.append(f"[{entry.category}] {entry.topic}")
        lines.append(f"  {entry.content[:200]}")
        lines.append(f"  Source: {entry.source} | Confidence: {entry.confidence:.0%}")
        lines.append("")
    return "\n".join(lines)


def _cog_autonomous_think(input_text: str) -> str:
    from cognition.autonomous import AutonomousReasoner
    reasoner = AutonomousReasoner()
    result = reasoner.think(input_text)
    lines = [
        f"=== Autonomous Reasoning ===",
        f"Thoughts generated: {result['total_thoughts']}",
        f"Overall confidence: {result['confidence']:.0%}\n",
        f"Observation: {result['observation'][:200]}",
        f"Analysis: {result['analysis'][:200]}",
        f"Decision: {result['decision'][:200]}",
        f"Reflection: {result['reflection'][:200]}",
        f"\nSynthesis: {result['synthesis'][:300]}",
    ]
    return "\n".join(lines)


def _cog_compare_sources(urls: str) -> str:
    import json
    from research.browser import EnhancedBrowser
    browser = EnhancedBrowser()
    url_list = [u.strip() for u in urls.split("\n") if u.strip()]
    if len(url_list) < 2:
        return "Need at least 2 URLs to compare."
    result = browser.compare_sources(url_list)
    lines = [
        f"=== Source Comparison ({result['sources']} sources) ===",
        f"Average word count: {result['avg_word_count']}",
        f"\nCommon terms: {', '.join(result['common_terms'][:15])}",
        "\nUnique points per source:",
    ]
    for url, points in result.get("unique_points", {}).items():
        lines.append(f"\n  {url}:")
        for p in points[:5]:
            lines.append(f"    - {p}")
    return "\n".join(lines)


def _cog_platform_info() -> str:
    from platforms.adapter import PlatformManager
    manager = PlatformManager()
    return manager.get_platform_report()


def _cog_security_scan(path: str = "") -> str:
    """Run security scan on codebase."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from security_subagent import SecuritySubAgent
        
        scan_path = Path(path) if path else Path.cwd()
        agent = SecuritySubAgent(str(scan_path))
        agent.scan_directory()
        
        summary = agent.get_summary()
        report = [
            "=== Security Audit Report ===",
            f"Total Issues: {summary['total']}",
            f"High Severity: {summary['high']}",
            f"Medium Severity: {summary['medium']}",
            f"Low Severity: {summary['low']}",
            f"Auto-fixable: {summary['auto_fixable']}",
            "",
        ]
        
        # Group by file
        by_file = {}
        for issue in agent.issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        for filepath, issues in sorted(by_file.items())[:10]:
            report.append(f"\n{filepath}:")
            for issue in issues[:5]:
                report.append(f"  [{issue.severity:6}] Line {issue.line}: {issue.issue}")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Security scan error: {e}"
