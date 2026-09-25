"""
Universal Platform Adapter — enables the agent to run across
desktop, web, mobile, CLI, and API platforms.
"""
from __future__ import annotations

import json
import platform
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class PlatformInfo:
    name: str
    os: str
    arch: str
    python_version: str
    ui_capabilities: list[str]
    input_methods: list[str]
    output_methods: list[str]
    network_available: bool
    file_system_access: bool
    voice_available: bool


class PlatformAdapter(ABC):
    """Base class for platform adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name."""

    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """Get platform information."""

    @abstractmethod
    def input(self, prompt: str = "") -> str:
        """Get user input."""

    @abstractmethod
    def output(self, text: str) -> None:
        """Display output to user."""

    @abstractmethod
    def output_rich(self, content: Any) -> None:
        """Display rich/formatted output."""

    def supports_feature(self, feature: str) -> bool:
        """Check if platform supports a feature."""
        return True


class CLIAdapter(PlatformAdapter):
    """Command-line interface adapter."""

    @property
    def name(self) -> str:
        return "cli"

    def get_platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            name="CLI",
            os=platform.system(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            ui_capabilities=["text", "colors", "markdown"],
            input_methods=["keyboard"],
            output_methods=["terminal", "file"],
            network_available=True,
            file_system_access=True,
            voice_available=False,
        )

    def input(self, prompt: str = "") -> str:
        try:
            from rich.prompt import Prompt
            return Prompt.ask(prompt) if prompt else input()
        except ImportError:
            return input(prompt)

    def output(self, text: str) -> None:
        print(text)

    def output_rich(self, content: Any) -> None:
        try:
            from rich.console import Console
            console = Console()
            console.print(content)
        except ImportError:
            print(content)

    def supports_feature(self, feature: str) -> bool:
        supported = {"text", "colors", "file_system", "network", "shell", "python_exec"}
        return feature in supported


class WebAdapter(PlatformAdapter):
    """Web interface adapter (Flask/FastAPI backend)."""

    def __init__(self) -> None:
        self._message_queue: list[dict[str, str]] = []

    @property
    def name(self) -> str:
        return "web"

    def get_platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Web",
            os=platform.system(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            ui_capabilities=["html", "css", "javascript", "markdown", "code_highlighting"],
            input_methods=["form", "websocket", "api"],
            output_methods=["html", "json", "websocket", "sse"],
            network_available=True,
            file_system_access=False,
            voice_available=False,
        )

    def input(self, prompt: str = "") -> str:
        return ""  # Web input handled via HTTP/WebSocket

    def output(self, text: str) -> None:
        self._message_queue.append({"type": "text", "content": text})

    def output_rich(self, content: Any) -> None:
        self._message_queue.append({"type": "rich", "content": str(content)})

    def supports_feature(self, feature: str) -> bool:
        supported = {"text", "html", "json", "websocket", "api", "markdown"}
        return feature in supported

    def get_messages(self) -> list[dict[str, str]]:
        msgs = self._message_queue.copy()
        self._message_queue.clear()
        return msgs

    def generate_api_endpoints(self) -> dict[str, str]:
        return {
            "POST /chat": "Send message to agent",
            "GET /history": "Get conversation history",
            "POST /tool": "Execute a tool directly",
            "GET /status": "Get agent status",
            "GET /tools": "List available tools",
        }


class DesktopAdapter(PlatformAdapter):
    """Desktop application adapter (Electron/Tkinter)."""

    @property
    def name(self) -> str:
        return "desktop"

    def get_platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Desktop",
            os=platform.system(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            ui_capabilities=["gui", "notification", "tray", "file_dialog", "clipboard"],
            input_methods=["keyboard", "mouse", "voice"],
            output_methods=["gui", "notification", "file"],
            network_available=True,
            file_system_access=True,
            voice_available=True,
        )

    def input(self, prompt: str = "") -> str:
        return input(prompt) if prompt else ""

    def output(self, text: str) -> None:
        print(text)

    def output_rich(self, content: Any) -> None:
        print(content)

    def supports_feature(self, feature: str) -> bool:
        supported = {
            "text", "gui", "notification", "tray", "file_system",
            "network", "clipboard", "voice", "shell", "python_exec",
        }
        return feature in supported


class MobileAdapter(PlatformAdapter):
    """Mobile application adapter."""

    @property
    def name(self) -> str:
        return "mobile"

    def get_platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Mobile",
            os=platform.system(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            ui_capabilities=["touch", "gesture", "notification", "camera", "gps"],
            input_methods=["touch", "voice", "keyboard"],
            output_methods=["screen", "notification", "vibration"],
            network_available=True,
            file_system_access=False,
            voice_available=True,
        )

    def input(self, prompt: str = "") -> str:
        return ""

    def output(self, text: str) -> None:
        pass

    def output_rich(self, content: Any) -> None:
        pass

    def supports_feature(self, feature: str) -> bool:
        supported = {"text", "touch", "notification", "voice", "network", "api"}
        return feature in supported


class APIAdapter(PlatformAdapter):
    """REST API adapter for integration."""

    def __init__(self) -> None:
        self._request_queue: list[dict[str, Any]] = []
        self._response_queue: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "api"

    def get_platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            name="API",
            os=platform.system(),
            arch=platform.machine(),
            python_version=platform.python_version(),
            ui_capabilities=["json", "rest", "graphql", "websocket"],
            input_methods=["http", "grpc", "websocket"],
            output_methods=["json", "xml", "yaml"],
            network_available=True,
            file_system_access=False,
            voice_available=False,
        )

    def input(self, prompt: str = "") -> str:
        return ""

    def output(self, text: str) -> None:
        self._response_queue.append({"type": "text", "content": text})

    def output_rich(self, content: Any) -> None:
        self._response_queue.append({"type": "json", "content": content})

    def supports_feature(self, feature: str) -> bool:
        supported = {"json", "rest", "api", "authentication", "rate_limiting"}
        return feature in supported


class PlatformManager:
    """Manages platform detection and adapter selection."""

    def __init__(self) -> None:
        self._adapters: dict[str, PlatformAdapter] = {
            "cli": CLIAdapter(),
            "web": WebAdapter(),
            "desktop": DesktopAdapter(),
            "mobile": MobileAdapter(),
            "api": APIAdapter(),
        }
        self._active_adapter: PlatformAdapter | None = None

    def detect_platform(self) -> str:
        """Auto-detect the current platform."""
        import sys
        if "web" in sys.modules or "flask" in sys.modules or "fastapi" in sys.modules:
            return "web"
        if "kivy" in sys.modules or "kivymd" in sys.modules:
            return "mobile"
        if "tkinter" in sys.modules or "PyQt" in sys.modules or "electron" in sys.modules:
            return "desktop"
        return "cli"

    def get_adapter(self, platform_name: str | None = None) -> PlatformAdapter:
        """Get adapter for specified or auto-detected platform."""
        name = platform_name or self.detect_platform()
        adapter = self._adapters.get(name, self._adapters["cli"])
        self._active_adapter = adapter
        return adapter

    def get_platform_report(self) -> str:
        """Generate a report of all platform capabilities."""
        lines = ["=== Platform Compatibility Report ===\n"]
        for name, adapter in self._adapters.items():
            info = adapter.get_platform_info()
            active = " (ACTIVE)" if adapter == self._active_adapter else ""
            lines.append(f"  {info.name}{active}")
            lines.append(f"    OS: {info.os} | Arch: {info.arch}")
            lines.append(f"    UI: {', '.join(info.ui_capabilities[:5])}")
            lines.append(f"    Input: {', '.join(info.input_methods)}")
            lines.append(f"    Output: {', '.join(info.output_methods)}")
            lines.append(f"    Network: {info.network_available} | FS: {info.file_system_access}")
            lines.append("")
        return "\n".join(lines)
