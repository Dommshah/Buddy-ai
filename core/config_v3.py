"""
Modern Agent Configuration — tool permissions, access control,
platform settings, and agent behavior configuration.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Permission(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class ToolCategory(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EDIT = "file_edit"
    BASH = "bash"
    GREP = "grep"
    GLOB = "glob"
    WEBFETCH = "webfetch"
    WEBSEARCH = "websearch"
    CODE_EXEC = "code_exec"
    NETWORK = "network"
    MEMORY = "memory"
    AGENT = "agent"
    VOICE = "voice"
    SECURITY = "security"
    DATA = "data"


@dataclass
class ToolPermission:
    tool_name: str
    permission: Permission
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    rate_limit: int = 0  # 0 = unlimited
    requires_confirmation: bool = False
    audit_log: bool = True


@dataclass
class AgentIdentity:
    name: str = "Agent"
    version: str = "3.0.0"
    owner: str = "Exclusive User"
    created: str = ""
    personality: str = "professional"
    voice_enabled: bool = True
    autonomous_mode: bool = True
    max_concurrent_agents: int = 5
    research_depth: int = 3  # 1=shallow, 5=deep
    creativity_level: float = 0.7
    security_level: str = "strict"  # strict, moderate, relaxed


@dataclass
class PlatformConfig:
    platform: str = "auto"  # auto, desktop, web, mobile, cli, api
    ui_framework: str = "auto"  # auto, rich, plain, web, terminal
    voice_input: bool = False
    voice_output: bool = False
    screen_reader: bool = False
    offline_mode: bool = False
    cache_responses: bool = True
    max_memory_mb: int = 512


@dataclass
class ResearchConfig:
    max_sources: int = 10
    depth: int = 3
    auto_cite: bool = True
    fact_check: bool = True
    cross_reference: bool = True
    preferred_sources: list[str] = field(default_factory=lambda: [
        "arxiv.org", "github.com", "stackoverflow.com",
        "docs.python.org", "developer.mozilla.org",
    ])
    blocked_sources: list[str] = field(default_factory=list)
    follow_links: bool = True
    max_page_depth: int = 3
    timeout_seconds: int = 30


@dataclass
class SubAgentConfig:
    enabled: bool = True
    max_depth: int = 3
    max_concurrent: int = 5
    timeout_seconds: int = 120
    auto_terminate: bool = True
    report_results: bool = True
    allowed_tools: list[str] = field(default_factory=lambda: [
        "read_file", "write_file", "search_files", "run_python",
        "web_search", "fetch_url", "code_analyze", "reason",
    ])


@dataclass
class AgentConfig:
    identity: AgentIdentity = field(default_factory=AgentIdentity)
    platform: PlatformConfig = field(default_factory=PlatformConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    sub_agents: SubAgentConfig = field(default_factory=SubAgentConfig)
    tool_permissions: dict[str, ToolPermission] = field(default_factory=dict)
    _config_path: Path = field(default_factory=lambda: Path("./data/agent_config.json"))

    def __post_init__(self) -> None:
        self._init_default_permissions()

    def _init_default_permissions(self) -> None:
        defaults = {
            "read_file": Permission.ALLOW,
            "write_file": Permission.ASK,
            "list_files": Permission.ALLOW,
            "search_files": Permission.ALLOW,
            "run_command": Permission.ASK,
            "run_python": Permission.ASK,
            "fetch_url": Permission.ALLOW,
            "web_search": Permission.ALLOW,
            "scrape_url": Permission.ASK,
            "save_memory": Permission.ALLOW,
            "recall_memory": Permission.ALLOW,
            "learn_store": Permission.ALLOW,
            "learn_recall": Permission.ALLOW,
            "security_audit": Permission.ALLOW,
            "code_analyze": Permission.ALLOW,
            "code_generate": Permission.ALLOW,
            "content_create": Permission.ALLOW,
            "creative_idea": Permission.ALLOW,
            "reason": Permission.ALLOW,
            "verify": Permission.ALLOW,
            "pattern_detect": Permission.ALLOW,
            "predict": Permission.ALLOW,
            "data_analyze": Permission.ALLOW,
            "voice_transcribe": Permission.ALLOW,
            "voice_listen": Permission.ALLOW,
            "voice_speak": Permission.ALLOW,
            "autonomy_plan": Permission.ALLOW,
            "autonomy_decide": Permission.ALLOW,
            "calculate": Permission.ALLOW,
            "json_query": Permission.ALLOW,
            "system_info": Permission.ALLOW,
            "get_datetime": Permission.ALLOW,
            "clipboard": Permission.ALLOW,
            "analyze_csv": Permission.ALLOW,
            "json_stats": Permission.ALLOW,
            "convert_format": Permission.ALLOW,
            "agent_spawn": Permission.ALLOW,
            "agent_delegate": Permission.ALLOW,
            "agent_status": Permission.ALLOW,
            "deep_research": Permission.ALLOW,
            "browse_page": Permission.ALLOW,
        }
        for tool_name, perm in defaults.items():
            if tool_name not in self.tool_permissions:
                self.tool_permissions[tool_name] = ToolPermission(
                    tool_name=tool_name, permission=perm
                )

    def check_permission(self, tool_name: str) -> Permission:
        """Check if a tool is allowed, needs confirmation, or is denied."""
        tp = self.tool_permissions.get(tool_name)
        if tp:
            return tp.permission
        return Permission.ASK

    def is_tool_allowed(self, tool_name: str) -> bool:
        return self.check_permission(tool_name) != Permission.DENY

    def requires_confirmation(self, tool_name: str) -> bool:
        return self.check_permission(tool_name) == Permission.ASK

    def set_permission(self, tool_name: str, permission: Permission) -> None:
        self.tool_permissions[tool_name] = ToolPermission(
            tool_name=tool_name, permission=permission
        )

    def bulk_set_permissions(self, category: ToolCategory, permission: Permission) -> None:
        category_tools = {
            ToolCategory.FILE_READ: ["read_file", "list_files", "search_files"],
            ToolCategory.FILE_WRITE: ["write_file"],
            ToolCategory.FILE_EDIT: ["write_file"],
            ToolCategory.BASH: ["run_command", "run_python"],
            ToolCategory.GREP: ["search_files"],
            ToolCategory.GLOB: ["list_files"],
            ToolCategory.WEBFETCH: ["fetch_url", "scrape_url", "browse_page"],
            ToolCategory.WEBSEARCH: ["web_search", "deep_research"],
            ToolCategory.CODE_EXEC: ["run_python", "run_command"],
            ToolCategory.NETWORK: ["fetch_url", "web_search", "scrape_url", "browse_page"],
            ToolCategory.MEMORY: ["save_memory", "recall_memory", "learn_store", "learn_recall"],
            ToolCategory.AGENT: ["agent_spawn", "agent_delegate", "agent_status"],
            ToolCategory.VOICE: ["voice_transcribe", "voice_listen", "voice_speak"],
            ToolCategory.SECURITY: ["security_audit", "code_analyze"],
            ToolCategory.DATA: ["data_analyze", "json_query", "calculate", "analyze_csv"],
        }
        for tool in category_tools.get(category, []):
            self.set_permission(tool, permission)

    def save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "identity": {
                "name": self.identity.name,
                "version": self.identity.version,
                "owner": self.identity.owner,
                "personality": self.identity.personality,
                "voice_enabled": self.identity.voice_enabled,
                "autonomous_mode": self.identity.autonomous_mode,
                "max_concurrent_agents": self.identity.max_concurrent_agents,
                "research_depth": self.identity.research_depth,
                "creativity_level": self.identity.creativity_level,
                "security_level": self.identity.security_level,
            },
            "platform": {
                "platform": self.platform.platform,
                "ui_framework": self.platform.ui_framework,
                "voice_input": self.platform.voice_input,
                "offline_mode": self.platform.offline_mode,
            },
            "research": {
                "max_sources": self.research.max_sources,
                "depth": self.research.depth,
                "auto_cite": self.research.auto_cite,
                "fact_check": self.research.fact_check,
            },
            "sub_agents": {
                "enabled": self.sub_agents.enabled,
                "max_depth": self.sub_agents.max_depth,
                "max_concurrent": self.sub_agents.max_concurrent,
            },
            "tool_permissions": {
                name: tp.permission.value
                for name, tp in self.tool_permissions.items()
            },
        }
        self._config_path.write_text(json.dumps(data, indent=2))

    def load(self) -> None:
        if not self._config_path.exists():
            return
        try:
            data = json.loads(self._config_path.read_text())
            if "identity" in data:
                for k, v in data["identity"].items():
                    if hasattr(self.identity, k):
                        setattr(self.identity, k, v)
            if "platform" in data:
                for k, v in data["platform"].items():
                    if hasattr(self.platform, k):
                        setattr(self.platform, k, v)
            if "research" in data:
                for k, v in data["research"].items():
                    if hasattr(self.research, k):
                        setattr(self.research, k, v)
            if "sub_agents" in data:
                for k, v in data["sub_agents"].items():
                    if hasattr(self.sub_agents, k):
                        setattr(self.sub_agents, k, v)
            if "tool_permissions" in data:
                for name, perm_str in data["tool_permissions"].items():
                    self.tool_permissions[name] = ToolPermission(
                        tool_name=name, permission=Permission(perm_str)
                    )
        except (json.JSONDecodeError, KeyError):
            pass

    def generate_config_summary(self) -> str:
        lines = [
            "=== Agent Configuration ===",
            f"Name: {self.identity.name} v{self.identity.version}",
            f"Owner: {self.identity.owner}",
            f"Platform: {self.platform.platform}",
            f"Security: {self.identity.security_level}",
            f"Autonomous: {self.identity.autonomous_mode}",
            f"Research Depth: {self.research.depth}/5",
            f"Max Sub-Agents: {self.sub_agents.max_concurrent}",
            "",
            "Tool Permissions:",
        ]
        by_permission = {"allow": [], "ask": [], "deny": []}
        for name, tp in self.tool_permissions.items():
            by_permission[tp.permission.value].append(name)

        for perm, tools in by_permission.items():
            if tools:
                lines.append(f"  {perm.upper()}: {', '.join(tools)}")

        return "\n".join(lines)
