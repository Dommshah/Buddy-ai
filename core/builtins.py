"""Buddy.ai — 49 built-in tools (File, System, Web, Memory, Cognition, Code, Content, Voice)."""
from __future__ import annotations

import glob
import threading
import os
import platform
import subprocess
import textwrap
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


    # ── COGNITIVE / REASONING TOOLS ──────────────────────────────────────

    registry.register(

        Tool(

            name="autonomous_reason",

            description="Run autonomous reasoning loop on a problem. Returns structured thoughts, analysis, and decision.",

            parameters={

                "type": "object",

                "properties": {

                    "prompt": {"type": "string", "description": "Problem or question to reason about"},

                    "mode": {"type": "string", "description": "Reasoning mode: auto, deductive, inductive, abductive, analogical, critical, reflective", "default": "auto"},

                    "max_steps": {"type": "integer", "description": "Maximum reasoning steps (default: 10)", "default": 10},

                },

                "required": ["prompt"],

            },

            execute=_cog_autonomous_reason,

        )

    )



    registry.register(

        Tool(

            name="reason",

            description="Apply structured reasoning mode to a problem. Supports chain-of-thought, tree-of-thought, deductive, inductive, abductive, analogical, critical, reflective.",

            parameters={

                "type": "object",

                "properties": {

                    "problem": {"type": "string", "description": "Problem statement"},

                    "mode": {"type": "string", "description": "Reasoning mode (default: chain_of_thought)", "default": "chain_of_thought"},

                },

                "required": ["problem"],

            },

            execute=_cog_reason,

        )

    )



    registry.register(

        Tool(

            name="verify",

            description="Verify a claim against evidence. Returns confidence score and reasoning.",

            parameters={

                "type": "object",

                "properties": {

                    "claim": {"type": "string", "description": "Claim to verify"},

                    "evidence": {"type": "string", "description": "Evidence/context for verification"},

                },

                "required": ["claim", "evidence"],

            },

            execute=_cog_verify,

        )

    )



    # ── SECURITY / CODE TOOLS ────────────────────────────────────────────

    registry.register(

        Tool(

            name="security_audit",

            description="Perform security audit on code or files. Detects vulnerabilities, hardcoded secrets, and security issues.",

            parameters={

                "type": "object",

                "properties": {

                    "path": {"type": "string", "description": "File or directory path to audit"},

                    "code": {"type": "string", "description": "Code string to audit (alternative to path)"},

                },

            },

            execute=_cog_security_scan,

        )

    )



    registry.register(

        Tool(

            name="code_analyze",

            description="Analyze code for complexity, issues, bugs, and maintainability. Supports Python, JavaScript, TypeScript.",

            parameters={

                "type": "object",

                "properties": {

                    "path": {"type": "string", "description": "File path to analyze"},

                    "code": {"type": "string", "description": "Code string to analyze (alternative to path)"},

                    "language": {"type": "string", "description": "Language: python, javascript, typescript (default: auto)", "default": "auto"},

                },

            },

            execute=_cog_code_analyze,

        )

    )



    registry.register(

        Tool(

            name="code_generate",

            description="Generate code from natural language description. Specify language and requirements.",

            parameters={

                "type": "object",

                "properties": {

                    "description": {"type": "string", "description": "What the code should do"},

                    "language": {"type": "string", "description": "Programming language (default: python)", "default": "python"},

                    "style": {"type": "string", "description": "Code style: concise, documented, production (default: production)", "default": "production"},

                },

                "required": ["description"],

            },

            execute=_cog_code_generate,

        )

    )



    # ── CONTENT CREATION TOOLS ──────────────────────────────────────────

    registry.register(

        Tool(

            name="content_create",

            description="Generate content: blog posts, emails, social media, landing pages, technical articles, product descriptions, press releases, reports, proposals, video scripts.",

            parameters={

                "type": "object",

                "properties": {

                    "type": {"type": "string", "description": "Content type: blog, email, social, landing, article, product, press, report, proposal, script"},

                    "topic": {"type": "string", "description": "Topic or subject"},

                    "tone": {"type": "string", "description": "Tone: professional, casual, persuasive, technical, creative (default: professional)", "default": "professional"},

                    "length": {"type": "string", "description": "Length: short, medium, long (default: medium)", "default": "medium"},

                    "context": {"type": "string", "description": "Additional context or requirements"},

                },

                "required": ["type", "topic"],

            },

            execute=_cog_content_create,

        )

    )



    # ── CREATIVITY TOOLS ────────────────────────────────────────────────

    registry.register(

        Tool(

            name="creative_idea",

            description="Generate creative ideas using SCAMPER, random association, analogical thinking, or innovation frameworks.",

            parameters={

                "type": "object",

                "properties": {

                    "prompt": {"type": "string", "description": "Creative challenge or prompt"},

                    "method": {"type": "string", "description": "Method: scamper, random, analogy, first_principles, morphing (default: scamper)", "default": "scamper"},

                    "count": {"type": "integer", "description": "Number of ideas (default: 5)", "default": 5},

                },

                "required": ["prompt"],

            },

            execute=_cog_creative_idea,

        )

    )



    registry.register(

        Tool(

            name="creative_prompt",

            description="Generate creative writing prompts by genre and mood.",

            parameters={

                "type": "object",

                "properties": {

                    "genre": {"type": "string", "description": "Genre: fiction, sci-fi, fantasy, mystery, romance, horror, non-fiction (default: any)", "default": "any"},

                    "mood": {"type": "string", "description": "Mood: dark, uplifting, mysterious, whimsical, gritty, cozy (default: any)", "default": "any"},

                },

            },

            execute=_cog_creative_prompt,

        )

    )



    # ── PATTERNS / PREDICTION TOOLS ──────────────────────────────────────

    registry.register(

        Tool(

            name="pattern_detect",

            description="Detect patterns in text or numerical data. Finds trends, cycles, anomalies, correlations.",

            parameters={

                "type": "object",

                "properties": {

                    "data": {"type": "string", "description": "Text or JSON array of numbers"},

                    "data_type": {"type": "string", "description": "text or numerical (default: text)", "default": "text"},

                },

                "required": ["data"],

            },

            execute=_cog_pattern_detect,

        )

    )



    registry.register(

        Tool(

            name="predict",

            description="Predict future values using linear regression, moving average, trend classification.",

            parameters={

                "type": "object",

                "properties": {

                    "values": {"type": "string", "description": "JSON array of numerical values"},

                    "steps_ahead": {"type": "integer", "description": "Steps to predict ahead (default: 3)", "default": 3},

                },

                "required": ["values"],

            },

            execute=_cog_predict,

        )

    )



    # ── VOICE TOOLS ──────────────────────────────────────────────────────

    registry.register(

        Tool(

            name="voice_speak",

            description="Convert text to speech using Texas Arknights RVC voice (preferred), gTTS, or pyttsx3.",

            parameters={

                "type": "object",

                "properties": {

                    "text": {"type": "string", "description": "Text to speak"},

                    "output_path": {"type": "string", "description": "Optional file path to save audio"},

                },

                "required": ["text"],

            },

            execute=_cog_voice_speak,

        )

    )



    registry.register(

        Tool(

            name="voice_listen",

            description="Listen to microphone and transcribe speech to text.",

            parameters={

                "type": "object",

                "properties": {

                    "timeout": {"type": "integer", "description": "Seconds to wait for speech (0=wait forever)", "default": 0},

                    "phrase_time_limit": {"type": "integer", "description": "Max seconds per phrase (0=unlimited)", "default": 0},

                },

            },

            execute=_cog_voice_listen,

        )

    )



    registry.register(

        Tool(

            name="voice_transcribe",

            description="Transcribe an audio file to text.",

            parameters={

                "type": "object",

                "properties": {

                    "audio_path": {"type": "string", "description": "Path to audio file"},

                },

                "required": ["audio_path"],

            },

            execute=_cog_voice_transcribe,

        )

    )



    registry.register(

        Tool(

            name="voice_engines",

            description="Get available TTS engines and their status.",

            parameters={},

            execute=_cog_voice_engines,

        )

    )



    # ── AGENT / RESEARCH TOOLS ──────────────────────────────────────────

    registry.register(

        Tool(

            name="agent_spawn",

            description="Spawn a specialized sub-agent (researcher, coder, analyzer, writer, reviewer, coordinator, custom).",

            parameters={

                "type": "object",

                "properties": {

                    "name": {"type": "string", "description": "Agent name"},

                    "role": {"type": "string", "description": "Role: researcher, coder, analyzer, writer, reviewer, coordinator, custom (default: custom)", "default": "custom"},

                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "List of capabilities"},

                },

                "required": ["name"],

            },

            execute=_cog_agent_spawn,

        )

    )



    registry.register(

        Tool(

            name="agent_delegate",

            description="Delegate a task to a spawned agent.",

            parameters={

                "type": "object",

                "properties": {

                    "agent_id": {"type": "string", "description": "ID of agent to delegate to"},

                    "task": {"type": "string", "description": "Task description"},

                },

                "required": ["agent_id", "task"],

            },

            execute=_cog_agent_delegate,

        )

    )



    registry.register(

        Tool(

            name="agent_status",

            description="Get status of all spawned agents.",

            parameters={},

            execute=_cog_agent_status,

        )

    )



    registry.register(

        Tool(

            name="deep_research",

            description="Perform deep multi-source web research with citations and synthesis.",

            parameters={

                "type": "object",

                "properties": {

                    "query": {"type": "string", "description": "Research query"},

                    "depth": {"type": "integer", "description": "Research depth 1-5 (default: 3)", "default": 3},

                    "max_sources": {"type": "integer", "description": "Maximum sources (default: 10)", "default": 10},

                },

                "required": ["query"],

            },

            execute=_cog_deep_research,

        )

    )



    registry.register(

        Tool(

            name="browse_page",

            description="Fetch and extract content from a web page with intelligent parsing.",

            parameters={

                "type": "object",

                "properties": {

                    "url": {"type": "string", "description": "URL to browse"},

                    "extract_text": {"type": "boolean", "description": "Extract text content (default: true)", "default": True},

                },

                "required": ["url"],

            },

            execute=_cog_browse_page,

        )

    )



    registry.register(

        Tool(

            name="web_search",

            description="Search the web using DuckDuckGo. Returns top results with snippets.",

            parameters={

                "type": "object",

                "properties": {

                    "query": {"type": "string", "description": "Search query"},

                    "num_results": {"type": "integer", "description": "Number of results (default: 5)", "default": 5},

                },

                "required": ["query"],

            },

            execute=_cog_web_search,

        )

    )



    # ── LEARNING / KNOWLEDGE TOOLS ──────────────────────────────────────

    registry.register(

        Tool(

            name="learn_store",

            description="Store a learned pattern or fact for future recall.",

            parameters={

                "type": "object",

                "properties": {

                    "category": {"type": "string", "description": "Category: preference, rule, fact, skill"},

                    "input_pattern": {"type": "string", "description": "Input pattern or trigger"},

                    "output": {"type": "string", "description": "Learned output or response"},

                    "confidence": {"type": "number", "description": "Confidence 0-1 (default: 0.8)", "default": 0.8},

                },

                "required": ["category", "input_pattern", "output"],

            },

            execute=_cog_learn_store,

        )

    )



    registry.register(

        Tool(

            name="learn_recall",

            description="Recall stored patterns or knowledge.",

            parameters={

                "type": "object",

                "properties": {

                    "category": {"type": "string", "description": "Filter by category"},

                    "query": {"type": "string", "description": "Search query"},

                },

            },

            execute=_cog_learn_recall,

        )

    )



    registry.register(

        Tool(

            name="knowledge_query",

            description="Query the knowledge base for structured information.",

            parameters={

                "type": "object",

                "properties": {

                    "topic": {"type": "string", "description": "Topic to search"},

                    "category": {"type": "string", "description": "Category filter"},

                },

                "required": ["topic"],

            },

            execute=_cog_knowledge_query,

        )

    )



    registry.register(

        Tool(

            name="knowledge_store",

            description="Store structured knowledge entry in the knowledge base.",

            parameters={

                "type": "object",

                "properties": {

                    "topic": {"type": "string", "description": "Topic name"},

                    "category": {"type": "string", "description": "Category"},

                    "content": {"type": "string", "description": "Content"},

                    "source": {"type": "string", "description": "Source"},

                    "confidence": {"type": "number", "description": "Confidence 0-1", "default": 0.9},

                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},

                },

                "required": ["topic", "category", "content", "source"],

            },

            execute=_cog_knowledge_store,

        )

    )



    # ── AUTONOMY TOOLS ──────────────────────────────────────────────────

    registry.register(

        Tool(

            name="autonomy_plan",

            description="Create an autonomous plan for a complex goal. Breaks down into steps with dependencies.",

            parameters={

                "type": "object",

                "properties": {

                    "goal": {"type": "string", "description": "Goal description"},

                    "context": {"type": "string", "description": "Current context or constraints"},

                },

                "required": ["goal"],

            },

            execute=_cog_autonomy_plan,

        )

    )



    registry.register(

        Tool(

            name="autonomy_decide",

            description="Make an autonomous decision based on options and criteria.",

            parameters={

                "type": "object",

                "properties": {

                    "situation": {"type": "string", "description": "Situation description"},

                    "options": {"type": "array", "items": {"type": "string"}, "description": "Available options"},

                    "criteria": {"type": "array", "items": {"type": "string"}, "description": "Decision criteria"},

                },

                "required": ["situation", "options"],

            },

            execute=_cog_autonomy_decide,

        )

    )



    # ── DATA ANALYSIS TOOLS ─────────────────────────────────────────────

    registry.register(

        Tool(

            name="analyze_csv",

            description="Analyze a CSV file — get stats, column info, and sample rows.",

            parameters={

                "type": "object",

                "properties": {

                    "path": {"type": "string", "description": "Path to CSV file"},

                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Specific columns to analyze"},

                },

                "required": ["path"],

            },

            execute=_cog_analyze_csv,

        )

    )



    registry.register(

        Tool(

            name="json_stats",

            description="Compute statistics for a field in a JSON array of objects.",

            parameters={

                "type": "object",

                "properties": {

                    "data": {"type": "string", "description": "JSON array string"},

                    "field_name": {"type": "string", "description": "Field to analyze"},

                },

                "required": ["data", "field_name"],

            },

            execute=_cog_json_stats,

        )

    )



    registry.register(

        Tool(

            name="convert_format",

            description="Convert between CSV and JSON formats.",

            parameters={

                "type": "object",

                "properties": {

                    "data": {"type": "string", "description": "Input data string"},

                    "from_format": {"type": "string", "description": "csv or json"},

                    "to_format": {"type": "string", "description": "csv or json"},

                },

                "required": ["data", "from_format", "to_format"],

            },

            execute=_cog_convert_format,

        )

    )



    # ── PLATFORM / ADAPTER TOOLS ────────────────────────────────────────

    registry.register(

        Tool(

            name="platform_adapter",

            description="Get platform-specific adapter info and capabilities.",

            parameters={

                "type": "object",

                "properties": {

                    "platform": {"type": "string", "description": "Platform: auto, desktop, web, mobile, cli, api (default: auto)", "default": "auto"},

                },

            },

            execute=_cog_platform_adapter,

        )

    )



    # ── PONYTAIL TOOLS ──────────────────────────────────────────────────

    registry.register(

        Tool(

            name="ponytail_set_mode",

            description="Set Ponytail lazy senior dev mode: lite, full, ultra, off.",

            parameters={

                "type": "object",

                "properties": {

                    "mode": {"type": "string", "description": "Mode: lite, full, ultra, off"},

                },

                "required": ["mode"],

            },

            execute=_cog_ponytail_set_mode,

        )

    )



    registry.register(

        Tool(

            name="ponytail_review",

            description="Review code for over-engineering, complexity, and YAGNI violations.",

            parameters={

                "type": "object",

                "properties": {

                    "code": {"type": "string", "description": "Code to review"},

                },

                "required": ["code"],

            },

            execute=_cog_ponytail_review,

        )

    )



    registry.register(

        Tool(

            name="ponytail_audit",

            description="Audit a file for over-engineering and complexity issues.",

            parameters={

                "type": "object",

                "properties": {

                    "path": {"type": "string", "description": "File path to audit"},

                },

                "required": ["path"],

            },

            execute=_cog_ponytail_audit,

        )

    )



    registry.register(

        Tool(

            name="ponytail_rules",

            description="Get the Ponytail lazy senior dev rules.",

            parameters={},

            execute=_cog_ponytail_rules,

        )

    )



    # ── VOICE ENGINE AVAILABILITY ──────────────────────────────────────

    registry.register(

        Tool(

            name="voice_engines",

            description="Get available TTS engines and their status.",

            parameters={},

            execute=_cog_voice_engines,

        )

    )



# ── Tool Implementations ────────────────────────────────────────────


def _read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found: {p}"
    if not p.is_file():
        return f"Error: Not a file: {p}"
    content = p.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    numbered = "\n".join(f"{i + 1:4}: {line}" for i, line in enumerate(lines))
    return f"File: {p} ({len(lines)} lines)\n\n{numbered}"


def _write_file(path: str, content: str) -> str:
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


def _run_command(command: str, cwd: str | None = None, timeout: int = 60) -> str:
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
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
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


def _fetch_url(url: str, method: str = "GET") -> str:
    import httpx

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.request(method, url)
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type:
                return resp.json()
            text = resp.text
            if len(text) > 10000:
                text = text[:10000] + f"\n\n... (truncated, {len(resp.text)} total chars)"
            return f"Status: {resp.status_code}\nContent-Type: {content_type}\n\n{text}"
    except Exception as e:
        return f"Error fetching URL: {e}"


def _get_datetime() -> str:
    now = datetime.now()
    return (
        f"Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
        f"Timestamp: {now.isoformat()}"
    )


def _save_memory(key: str, value: str, category: str = "note") -> str:
    import json

    memory_dir = Path("./data/memory")
    memory_dir.mkdir(parents=True, exist_ok=True)
    mem_file = memory_dir / "memories.json"

    memories: dict[str, Any] = {}
    if mem_file.exists():
        memories = json.loads(mem_file.read_text())

    memories[key] = {"value": value, "category": category, "updated": datetime.now().isoformat()}
    mem_file.write_text(json.dumps(memories, indent=2))
    return f"Saved to memory: '{key}' (category: {category})"


def _recall_memory(key: str | None = None, category: str | None = None) -> str:
    import json

    mem_file = Path("./data/memory/memories.json")
    if not mem_file.exists():
        return "No memories stored yet."

    memories = json.loads(mem_file.read_text())

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
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        exec_globals: dict[str, Any] = {"__builtins__": __builtins__}
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compile(code, "<agent>", "exec"), exec_globals)

        output = ""
        if stdout_capture.getvalue():
            output += f"STDOUT:\n{stdout_capture.getvalue()}\n"
        if stderr_capture.getvalue():
            output += f"STDERR:\n{stderr_capture.getvalue()}\n"
        return output or "Code executed successfully (no output)."
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

    def _eval(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in safe_ops:
            return safe_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in safe_ops:
            return safe_ops[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression")

    try:
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

# ── COGNITIVE / REASONING TOOLS ──────────────────────────────────────

    registry.register(
        Tool(
            name="autonomous_reason",
            description="Run autonomous reasoning loop on a problem. Returns structured thoughts, analysis, and decision.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Problem or question to reason about"},
                    "mode": {"type": "string", "description": "Reasoning mode: auto, deductive, inductive, abductive, analogical, critical, reflective", "default": "auto"},
                    "max_steps": {"type": "integer", "description": "Maximum reasoning steps (default: 10)", "default": 10},
                },
                "required": ["prompt"],
            },
            execute=_cog_autonomous_reason,
        )
    )

    registry.register(
        Tool(
            name="reason",
            description="Apply structured reasoning mode to a problem. Supports chain-of-thought, tree-of-thought, deductive, inductive, abductive, analogical, critical, reflective.",
            parameters={
                "type": "object",
                "properties": {
                    "problem": {"type": "string", "description": "Problem statement"},
                    "mode": {"type": "string", "description": "Reasoning mode (default: chain_of_thought)", "default": "chain_of_thought"},
                },
                "required": ["problem"],
            },
            execute=_cog_reason,
        )
    )

    registry.register(
        Tool(
            name="verify",
            description="Verify a claim against evidence. Returns confidence score and reasoning.",
            parameters={
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "Claim to verify"},
                    "evidence": {"type": "string", "description": "Evidence/context for verification"},
                },
                "required": ["claim", "evidence"],
            },
            execute=_cog_verify,
        )
    )

# ── SECURITY / CODE TOOLS ────────────────────────────────────────────

    registry.register(
        Tool(
            name="security_audit",
            description="Perform security audit on code or files. Detects vulnerabilities, hardcoded secrets, and security issues.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or directory path to audit"},
                    "code": {"type": "string", "description": "Code string to audit (alternative to path)"},
                },
            },
            execute=_cog_security_scan,
        )
    )

    registry.register(
        Tool(
            name="code_analyze",
            description="Analyze code for complexity, issues, bugs, and maintainability. Supports Python, JavaScript, TypeScript.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to analyze"},
                    "code": {"type": "string", "description": "Code string to analyze (alternative to path)"},
                    "language": {"type": "string", "description": "Language: python, javascript, typescript (default: auto)", "default": "auto"},
                },
            },
            execute=_cog_code_analyze,
        )
    )

    registry.register(
        Tool(
            name="code_generate",
            description="Generate code from natural language description. Specify language and requirements.",
            parameters={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the code should do"},
                    "language": {"type": "string", "description": "Programming language (default: python)", "default": "python"},
                    "style": {"type": "string", "description": "Code style: concise, documented, production (default: production)", "default": "production"},
                },
                "required": ["description"],
            },
            execute=_cog_code_generate,
        )
    )

# ── CONTENT CREATION TOOLS ──────────────────────────────────────────

    registry.register(
        Tool(
            name="content_create",
            description="Generate content: blog posts, emails, social media, landing pages, technical articles, product descriptions, press releases, reports, proposals, video scripts.",
            parameters={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Content type: blog, email, social, landing, article, product, press, report, proposal, script"},
                    "topic": {"type": "string", "description": "Topic or subject"},
                    "tone": {"type": "string", "description": "Tone: professional, casual, persuasive, technical, creative (default: professional)", "default": "professional"},
                    "length": {"type": "string", "description": "Length: short, medium, long (default: medium)", "default": "medium"},
                    "context": {"type": "string", "description": "Additional context or requirements"},
                },
                "required": ["type", "topic"],
            },
            execute=_cog_content_create,
        )
    )

# ── CREATIVITY TOOLS ────────────────────────────────────────────────

    registry.register(
        Tool(
            name="creative_idea",
            description="Generate creative ideas using SCAMPER, random association, analogical thinking, or innovation frameworks.",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Creative challenge or prompt"},
                    "method": {"type": "string", "description": "Method: scamper, random, analogy, first_principles, morphing (default: scamper)", "default": "scamper"},
                    "count": {"type": "integer", "description": "Number of ideas (default: 5)", "default": 5},
                },
                "required": ["prompt"],
            },
            execute=_cog_creative_idea,
        )
    )

    registry.register(
        Tool(
            name="creative_prompt",
            description="Generate creative writing prompts by genre and mood.",
            parameters={
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre: fiction, sci-fi, fantasy, mystery, romance, horror, non-fiction (default: any)", "default": "any"},
                    "mood": {"type": "string", "description": "Mood: dark, uplifting, mysterious, whimsical, gritty, cozy (default: any)", "default": "any"},
                },
            },
            execute=_cog_creative_prompt,
        )
    )

# ── PATTERNS / PREDICTION TOOLS ──────────────────────────────────────

    registry.register(
        Tool(
            name="pattern_detect",
            description="Detect patterns in text or numerical data. Finds trends, cycles, anomalies, correlations.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Text or JSON array of numbers"},
                    "data_type": {"type": "string", "description": "text or numerical (default: text)", "default": "text"},
                },
                "required": ["data"],
            },
            execute=_cog_pattern_detect,
        )
    )

    registry.register(
        Tool(
            name="predict",
            description="Predict future values using linear regression, moving average, trend classification.",
            parameters={
                "type": "object",
                "properties": {
                    "values": {"type": "string", "description": "JSON array of numerical values"},
                    "steps_ahead": {"type": "integer", "description": "Steps to predict ahead (default: 3)", "default": 3},
                },
                "required": ["values"],
            },
            execute=_cog_predict,
        )
    )

# ── VOICE TOOLS ──────────────────────────────────────────────────────

    registry.register(
        Tool(
            name="voice_speak",
            description="Convert text to speech using Texas Arknights RVC voice (preferred), gTTS, or pyttsx3.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to speak"},
                    "output_path": {"type": "string", "description": "Optional file path to save audio"},
                },
                "required": ["text"],
            },
            execute=_cog_voice_speak,
        )
    )

    registry.register(
        Tool(
            name="voice_listen",
            description="Listen to microphone and transcribe speech to text.",
            parameters={
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer", "description": "Seconds to wait for speech (0=wait forever)", "default": 0},
                    "phrase_time_limit": {"type": "integer", "description": "Max seconds per phrase (0=unlimited)", "default": 0},
                },
            },
            execute=_cog_voice_listen,
        )
    )

    registry.register(
        Tool(
            name="voice_transcribe",
            description="Transcribe an audio file to text.",
            parameters={
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string", "description": "Path to audio file"},
                },
                "required": ["audio_path"],
            },
            execute=_cog_voice_transcribe,
        )
    )

# ── AGENT / RESEARCH TOOLS ──────────────────────────────────────────

    registry.register(
        Tool(
            name="agent_spawn",
            description="Spawn a specialized sub-agent (researcher, coder, analyzer, writer, reviewer, coordinator, custom).",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name"},
                    "role": {"type": "string", "description": "Role: researcher, coder, analyzer, writer, reviewer, coordinator, custom (default: custom)", "default": "custom"},
                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "List of capabilities"},
                },
                "required": ["name"],
            },
            execute=_cog_agent_spawn,
        )
    )

    registry.register(
        Tool(
            name="agent_delegate",
            description="Delegate a task to a spawned agent.",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "ID of agent to delegate to"},
                    "task": {"type": "string", "description": "Task description"},
                },
                "required": ["agent_id", "task"],
            },
            execute=_cog_agent_delegate,
        )
    )

    registry.register(
        Tool(
            name="agent_status",
            description="Get status of all spawned agents.",
            parameters={},
            execute=_cog_agent_status,
        )
    )

    registry.register(
        Tool(
            name="deep_research",
            description="Perform deep multi-source web research with citations and synthesis.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Research query"},
                    "depth": {"type": "integer", "description": "Research depth 1-5 (default: 3)", "default": 3},
                    "max_sources": {"type": "integer", "description": "Maximum sources (default: 10)", "default": 10},
                },
                "required": ["query"],
            },
            execute=_cog_deep_research,
        )
    )

    registry.register(
        Tool(
            name="browse_page",
            description="Fetch and extract content from a web page with intelligent parsing.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to browse"},
                    "extract_text": {"type": "boolean", "description": "Extract text content (default: true)", "default": True},
                },
                "required": ["url"],
            },
            execute=_cog_browse_page,
        )
    )

    registry.register(
        Tool(
            name="web_search",
            description="Search the web using DuckDuckGo. Returns top results with snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results (default: 5)", "default": 5},
                },
                "required": ["query"],
            },
            execute=_cog_web_search,
        )
    )

# ── LEARNING / KNOWLEDGE TOOLS ──────────────────────────────────────

    registry.register(
        Tool(
            name="learn_store",
            description="Store a learned pattern or fact for future recall.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category: preference, rule, fact, skill"},
                    "input_pattern": {"type": "string", "description": "Input pattern or trigger"},
                    "output": {"type": "string", "description": "Learned output or response"},
                    "confidence": {"type": "number", "description": "Confidence 0-1 (default: 0.8)", "default": 0.8},
                },
                "required": ["category", "input_pattern", "output"],
            },
            execute=_cog_learn_store,
        )
    )

    registry.register(
        Tool(
            name="learn_recall",
            description="Recall stored patterns or knowledge.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                    "query": {"type": "string", "description": "Search query"},
                },
            },
            execute=_cog_learn_recall,
        )
    )

    registry.register(
        Tool(
            name="knowledge_query",
            description="Query the knowledge base for structured information.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to search"},
                    "category": {"type": "string", "description": "Category filter"},
                },
                "required": ["topic"],
            },
            execute=_cog_knowledge_query,
        )
    )

    registry.register(
        Tool(
            name="knowledge_store",
            description="Store structured knowledge entry in the knowledge base.",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic name"},
                    "category": {"type": "string", "description": "Category"},
                    "content": {"type": "string", "description": "Content"},
                    "source": {"type": "string", "description": "Source"},
                    "confidence": {"type": "number", "description": "Confidence 0-1", "default": 0.9},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                },
                "required": ["topic", "category", "content", "source"],
            },
            execute=_cog_knowledge_store,
        )
    )

# ── AUTONOMY TOOLS ──────────────────────────────────────────────────

    registry.register(
        Tool(
            name="autonomy_plan",
            description="Create an autonomous plan for a complex goal. Breaks down into steps with dependencies.",
            parameters={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "Goal description"},
                    "context": {"type": "string", "description": "Current context or constraints"},
                },
                "required": ["goal"],
            },
            execute=_cog_autonomy_plan,
        )
    )

    registry.register(
        Tool(
            name="autonomy_decide",
            description="Make an autonomous decision based on options and criteria.",
            parameters={
                "type": "object",
                "properties": {
                    "situation": {"type": "string", "description": "Situation description"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "Available options"},
                    "criteria": {"type": "array", "items": {"type": "string"}, "description": "Decision criteria"},
                },
                "required": ["situation", "options"],
            },
            execute=_cog_autonomy_decide,
        )
    )

# ── DATA ANALYSIS TOOLS ─────────────────────────────────────────────

    registry.register(
        Tool(
            name="analyze_csv",
            description="Analyze a CSV file — get stats, column info, and sample rows.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to CSV file"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Specific columns to analyze"},
                },
                "required": ["path"],
            },
            execute=_cog_analyze_csv,
        )
    )

    registry.register(
        Tool(
            name="json_stats",
            description="Compute statistics for a field in a JSON array of objects.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "JSON array string"},
                    "field_name": {"type": "string", "description": "Field to analyze"},
                },
                "required": ["data", "field_name"],
            },
            execute=_cog_json_stats,
        )
    )

    registry.register(
        Tool(
            name="convert_format",
            description="Convert between CSV and JSON formats.",
            parameters={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Input data string"},
                    "from_format": {"type": "string", "description": "csv or json"},
                    "to_format": {"type": "string", "description": "csv or json"},
                },
                "required": ["data", "from_format", "to_format"],
            },
            execute=_cog_convert_format,
        )
    )

# ── PLATFORM / ADAPTER TOOLS ────────────────────────────────────────

    registry.register(
        Tool(
            name="platform_adapter",
            description="Get platform-specific adapter info and capabilities.",
            parameters={
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Platform: auto, desktop, web, mobile, cli, api (default: auto)", "default": "auto"},
                },
            },
            execute=_cog_platform_adapter,
        )
    )

# ── PONYTAIL TOOLS ──────────────────────────────────────────────────

    registry.register(
        Tool(
            name="ponytail_set_mode",
            description="Set Ponytail lazy senior dev mode: lite, full, ultra, off.",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "description": "Mode: lite, full, ultra, off"},
                },
                "required": ["mode"],
            },
            execute=_cog_ponytail_set_mode,
        )
    )

    registry.register(
        Tool(
            name="ponytail_review",
            description="Review code for over-engineering, complexity, and YAGNI violations.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                },
                "required": ["code"],
            },
            execute=_cog_ponytail_review,
        )
    )

    registry.register(
        Tool(
            name="ponytail_audit",
            description="Audit a file for over-engineering and complexity issues.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to audit"},
                },
                "required": ["path"],
            },
            execute=_cog_ponytail_audit,
        )
    )

    registry.register(
        Tool(
            name="ponytail_rules",
            description="Get the Ponytail lazy senior dev rules.",
            parameters={},
            execute=_cog_ponytail_rules,
        )
    )

# ── VOICE ENGINE AVAILABILITY ──────────────────────────────────────

    registry.register(
        Tool(
            name="voice_engines",
            description="Get available TTS engines and their status.",
            parameters={},
            execute=_cog_voice_engines,
        )
    )

# ── EXECUTION IMPLEMENTATIONS ───────────────────────────────────────


def _cog_autonomous_reason(prompt: str, mode: str = "auto", max_steps: int = 10) -> str:
    from cognition.autonomy import AutonomousReasoner
    reasoner = AutonomousReasoner()
    result = reasoner.think(prompt, mode=mode, max_steps=max_steps)
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


def _cog_reason(problem: str, mode: str = "chain_of_thought") -> str:
    from cognition.reasoning import ReasoningEngine
    engine = ReasoningEngine()
    result = engine.reason(problem, mode)
    return f"=== {mode.replace('_', ' ').title()} ===\n{result}"


def _cog_verify(claim: str, evidence: str) -> str:
    from cognition.verification import VerificationEngine
    engine = VerificationEngine()
    result = engine.verify(claim, evidence)
    lines = [
        f"=== Verification Result ===",
        f"Claim: {claim}",
        f"Verdict: {result['verdict']}",
        f"Confidence: {result['confidence']:.0%}",
        f"Reasoning: {result['reasoning']}",
    ]
    return "\n".join(lines)


def _cog_security_scan(path: str = "") -> str:
    """Run security scan on codebase."""
    try:
        from security_subagent import SecuritySubAgent
        scan_path = Path(path) if path else Path.cwd()
        agent = SecuritySubAgent(str(scan_path))
        agent.scan_directory()
        return agent.generate_report()
    except Exception as e:
        return f"Security scan error: {e}"


def _cog_code_analyze(path: str = "", code: str = "", language: str = "auto") -> str:
    from cognition.code_analysis import CodeAnalyzer
    analyzer = CodeAnalyzer()
    if path:
        result = analyzer.analyze_file(path)
    elif code:
        result = analyzer.analyze_code(code, language)
    else:
        return "Error: Provide either path or code"
    lines = [f"=== Code Analysis ===", f"File: {result.get('file', 'input')}", f"Language: {result['language']}", f"Lines: {result['lines']}", f"Functions: {result['functions']}", f"Classes: {result['classes']}", f"Complexity: {result['complexity']:.1f}", f"Issues: {len(result['issues'])}", ""]
    for issue in result['issues'][:10]:
        lines.append(f"  [{issue['severity']}] Line {issue['line']}: {issue['message']}")
    return "\n".join(lines)


def _cog_code_generate(description: str, language: str = "python", style: str = "production") -> str:
    from cognition.code_analysis import CodeGenerator
    generator = CodeGenerator()
    result = generator.generate(description, language, style)
    return result.get("code", f"Generation failed: {result.get('error', 'Unknown')}")


def _cog_content_create(type: str, topic: str, tone: str = "professional", length: str = "medium", context: str = "") -> str:
    from cognition.content import ContentCreator
    creator = ContentCreator()
    result = creator.create(type, topic, tone, length, context)
    return result


def _cog_creative_idea(prompt: str, method: str = "scamper", count: int = 5) -> str:
    from cognition.creativity import CreativityEngine
    engine = CreativityEngine()
    ideas = engine.generate_ideas(prompt, method, count)
    lines = [f"=== Creative Ideas ({method}) ===", f"Prompt: {prompt}\n"]
    for i, idea in enumerate(ideas, 1):
        lines.append(f"{i}. {idea}")
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
            values = safe_json_loads(data)
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
    engine = PredictionEngine()
    try:
        nums = safe_json_loads(values)
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


def _cog_voice_speak(text: str, output_path: str = "") -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.speak(text, output_path)
    if result.get("success"):
        return f"DONE_SPEAKING: Text spoken successfully. Do NOT call voice_speak again."
    return f"TTS_ERROR: {result.get('error', 'Unknown error')}"


def _cog_voice_listen(timeout: int = 0, phrase_time_limit: int = 0) -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)
    if result.get("success"):
        return f"HEARD ({result.get('engine', 'unknown')}): {result['text']}"
    return f"LISTEN_ERROR: {result.get('error', 'Unknown error')}"


def _cog_voice_transcribe(audio_path: str) -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    result = vr.transcribe_audio(audio_path)
    if result.get("success"):
        return result["text"]
    return f"TRANSCRIBE_ERROR: {result.get('error', 'Unknown error')}"


def _cog_voice_engines() -> str:
    from cognition.voice import VoiceRecognition
    vr = VoiceRecognition()
    status = vr.get_status()
    engines = status.get("engines", {})
    lines = ["=== Voice Engines ==="]
    for name, available in engines.items():
        lines.append(f"  {name}: {'✓' if available else '✗'}")
    return "\n".join(lines)


def _cog_agent_spawn(name: str, role: str = "custom", capabilities: list[str] | None = None) -> str:
    from agents.orchestrator import AgentOrchestrator, AgentRole
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
    agent_id = orch.spawn_agent(name, role_enum, capabilities or [])
    return f"Agent spawned: {name} ({role}) — ID: {agent_id}"


def _cog_agent_delegate(agent_id: str, task: str) -> str:
    from agents.orchestrator import AgentOrchestrator
    orch = _get_orchestrator()
    try:
        orch.delegate_task(agent_id, task)
        return f"Task delegated to agent {agent_id}"
    except Exception as e:
        return f"Delegation failed: {e}"


def _cog_agent_status() -> str:
    from agents.orchestrator import AgentOrchestrator
    orch = _get_orchestrator()
    status = orch.get_status()
    lines = [f"=== Agent Fleet ({status['total_agents']} agents) ==="]
    for agent in status['agents']:
        lines.append(f"  [{agent['role']:12}] {agent['name']} — Tasks: {agent['completed']}✅ {agent['failed']}❌ {agent['pending']}⏳ | State: {agent['state']}")
    return "\n".join(lines)


def _cog_deep_research(query: str, depth: int = 3, max_sources: int = 10) -> str:
    from research.engine import DeepResearchEngine
    engine = DeepResearchEngine()
    result = engine.research(query, depth=depth, max_sources=max_sources)
    lines = [
        f"=== Deep Research ===",
        f"Query: {query}",
        f"Sources: {len(result.sources)}",
        f"Words: {result.total_words:,}",
        f"Confidence: {result.confidence:.0%}\n",
        f"Summary:\n{result.summary[:500]}",
        f"\nKey Findings:",
    ]
    for finding in result.key_findings[:10]:
        lines.append(f"  • {finding}")
    lines.append(f"\nCitations: {len(result.citations)}")
    return "\n".join(lines)


def _cog_browse_page(url: str, extract_text: bool = True) -> str:
    from research.browser import EnhancedBrowser
    browser = EnhancedBrowser()
    page = browser.fetch_page(url, extract_text)
    if page.status_code != 200:
        return f"HTTP {page.status_code}: {page.content[:200]}"
    lines = [
        f"=== Page: {page.title} ===",
        f"URL: {page.url}",
        f"Words: {page.word_count}",
        f"Language: {page.language}\n",
        page.content[:2000] + ("..." if len(page.content) > 2000 else ""),
    ]
    return "\n".join(lines)


def _cog_web_search(query: str, num_results: int = 5) -> str:
    from plugins.web import WebSearchPlugin
    from core.tools import ToolRegistry
    plugin = WebSearchPlugin()
    return plugin._search(query, num_results)


def _cog_learn_store(category: str, input_pattern: str, output: str, confidence: float = 0.8) -> str:
    from cognition.learning.adaptive import LearningSystem
    system = LearningSystem()
    entry_id = system.store_pattern(category, input_pattern, output, confidence)
    return f"Stored pattern: {entry_id} (category: {category}, confidence: {confidence:.0%})"


def _cog_learn_recall(category: str | None = None, query: str | None = None) -> str:
    from cognition.learning.adaptive import LearningSystem
    system = LearningSystem()
    if query:
        results = system.recall(query, category)
    else:
        results = system.get_patterns(category)
    if not results:
        return "No matching patterns found."
    lines = [f"=== Recalled Patterns ({len(results)}) ==="]
    for r in results[:10]:
        lines.append(f"  [{r.category}] {r.input_pattern} → {r.learned_output} (conf: {r.confidence:.0%}, used: {r.times_used})")
    return "\n".join(lines)


def _cog_knowledge_query(topic: str, category: str | None = None) -> str:
    from knowledge.base import KnowledgeBase
    kb = KnowledgeBase()
    results = kb.search(topic, category)
    if not results:
        return f"No knowledge found for: {topic}"
    lines = [f"=== Knowledge: {topic} ==="]
    for entry in results[:5]:
        lines.append(f"\n[{entry.category}] {entry.topic}")
        lines.append(f"  Source: {entry.source} | Confidence: {entry.confidence:.0%}")
        lines.append(f"  {entry.content[:200]}")
    return "\n".join(lines)


def _cog_knowledge_store(topic: str, category: str, content: str, source: str, confidence: float = 0.9, tags: list[str] | None = None) -> str:
    from knowledge.base import KnowledgeBase
    kb = KnowledgeBase()
    entry_id = kb.add_entry(topic, category, content, source, confidence, tags or [])
    return f"Stored knowledge: {entry_id}"


def _cog_autonomy_plan(goal: str, context: str = "") -> str:
    from cognition.autonomy import AutonomyEngine
    engine = AutonomyEngine()
    plan = engine.create_plan(goal, context)
    lines = [f"=== Autonomous Plan ===", f"Goal: {goal}", f"Steps: {len(plan.steps)}", f"Estimated time: {plan.estimated_time}\n"]
    for i, step in enumerate(plan.steps, 1):
        deps = f" (depends on: {', '.join(map(str, step.dependencies))})" if step.dependencies else ""
        lines.append(f"  {i}. {step.description}{deps}")
    return "\n".join(lines)


def _cog_autonomy_decide(situation: str, options: list[str], criteria: list[str] | None = None) -> str:
    from cognition.autonomy import AutonomyEngine
    engine = AutonomyEngine()
    result = engine.decide(situation, options, criteria or [])
    lines = [
        f"=== Decision ===",
        f"Situation: {situation}",
        f"Chosen: {result['chosen']}",
        f"Reasoning: {result['reasoning']}",
        f"Confidence: {result['confidence']:.0%}",
    ]
    if result.get("scores"):
        lines.append("\nScores:")
        for opt, score in result['scores'].items():
            lines.append(f"  {opt}: {score:.2f}")
    return "\n".join(lines)


def _cog_analyze_csv(path: str, columns: list[str] | None = None) -> str:
    from plugins.data import DataAnalysisPlugin
    plugin = DataAnalysisPlugin()
    return plugin._analyze_csv(path, columns)


def _cog_json_stats(data: str, field_name: str) -> str:
    from plugins.data import DataAnalysisPlugin
    plugin = DataAnalysisPlugin()
    return plugin._json_stats(data, field_name)


def _cog_convert_format(data: str, from_format: str, to_format: str) -> str:
    from plugins.data import DataAnalysisPlugin
    plugin = DataAnalysisPlugin()
    return plugin._convert_format(data, from_format, to_format)


def _cog_platform_adapter(platform: str = "auto") -> str:
    from platforms.adapter import PlatformAdapterFactory
    adapter = PlatformAdapterFactory.create(platform)
    return adapter.get_platform_report()


def _cog_ponytail_set_mode(mode: str) -> str:
    from ponytail import set_mode
    result = set_mode(mode)
    return f"DONE: {result}. Do NOT call ponytail_set_mode again."


def _cog_ponytail_review(code: str) -> str:
    from ponytail import review_code
    result = review_code(code)
    lines = [
        "=== Ponytail Code Review ===",
        f"Mode: {result['mode']}",
        f"Verdict: {result['verdict']}",
        "",
    ]
    if result['issues']:
        lines.append("Issues Found:")
        for issue in result['issues']:
            lines.append(f"  ⚠ {issue}")
    if result['suggestions']:
        lines.append("\nSuggestions:")
        for suggestion in result['suggestions']:
            lines.append(f"  💡 {suggestion}")
    if not result['issues'] and not result['suggestions']:
        lines.append("✓ No over-engineering detected")
    return "\n".join(lines)


def _cog_ponytail_audit(path: str) -> str:
    from ponytail import audit_file
    result = audit_file(path)
    if "error" in result:
        return f"Ponytail audit error: {result['error']}"
    lines = [
        "=== Ponytail File Audit ===",
        f"File: {result.get('file', path)}",
        f"Lines: {result.get('lines', 0)}",
        f"Mode: {result['mode']}",
        f"Verdict: {result['verdict']}",
        "",
    ]
    if result.get('issues'):
        lines.append("Issues Found:")
        for issue in result['issues']:
            lines.append(f"  ⚠ {issue}")
    if result.get('suggestions'):
        lines.append("\nSuggestions:")
        for suggestion in result['suggestions']:
            lines.append(f"  💡 {suggestion}")
    if not result.get('issues') and not result.get('suggestions'):
        lines.append("✓ No over-engineering detected")
    return "\n".join(lines)


def _cog_ponytail_rules() -> str:
    from ponytail import get_rules
    return get_rules()


# Module-level singleton for orchestrator
_orchestrator = None
_orchestrator_lock = threading.Lock()


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        with _orchestrator_lock:
            if _orchestrator is None:
                from agents.orchestrator import AgentOrchestrator
                _orchestrator = AgentOrchestrator(max_agents=5)
    return _orchestrator


