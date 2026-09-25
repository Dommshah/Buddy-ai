"""Main Agent class — Buddy.ai vibrant interactive experience."""
from __future__ import annotations

import logging
import time as _time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.styles import Style

from .config import Config
from .engine import AgentEngine
from .tools import ToolRegistry
from . import ui

MODELS = {
    "1": ("gemini-3.5-flash-lite", "Fast & Efficient (Recommended)"),
    "2": ("gemini-3.6-flash", "Balanced (20 requests/day limit)"),
    "3": ("gemini-3.1-pro-preview", "Most Capable (Quota limited)"),
    "4": ("qwen2.5:3b", "Offline (Ollama) — No internet needed"),
}

DEFAULT_MODEL = "gemini-3.5-flash-lite"


def select_model() -> str:
    """Display model selection menu and return chosen model."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False

    if use_rich:
        console.print()
        table = Table(title="Select Buddy Model", show_header=True, header_style="bold cyan")
        table.add_column("Option", style="bold yellow", width=8)
        table.add_column("Model", style="bold white", width=20)
        table.add_column("Description", style="dim")
        for key, (model, desc) in MODELS.items():
            table.add_row(key, model, desc)
        console.print(table)
        console.print(f"\n[dim]Default: {DEFAULT_MODEL}[/]")
        console.print("[dim]Press Enter to use default, or type a number (1-4)[/]")
        console.print()
    else:
        print("\n=== Select Buddy Model ===")
        for key, (model, desc) in MODELS.items():
            print(f"  {key}. {model} — {desc}")
        print(f"\nDefault: {DEFAULT_MODEL}")
        print("Press Enter to use default, or type a number (1-4)\n")

    try:
        from prompt_toolkit import PromptSession
        prompt_session = PromptSession()
        use_prompt_toolkit = True
    except ImportError:
        use_prompt_toolkit = False

    while True:
        try:
            if use_prompt_toolkit:
                choice = prompt_session.prompt("Choose model (or press Enter for default): ").strip()
            elif use_rich:
                from rich.prompt import Prompt
                choice = Prompt.ask("[bold yellow]Choose model[/]", default="")
            else:
                choice = input("Choose model (or press Enter for default): ").strip()

            if choice == "":
                selected = DEFAULT_MODEL
                break
            elif choice in MODELS:
                selected = MODELS[choice][0]
                break
            else:
                if use_rich:
                    console.print("[red]Invalid choice. Please enter 1, 2, 3, or 4.[/]")
                else:
                    print("Invalid choice. Please enter 1, 2, 3, or 4.")
        except (KeyboardInterrupt, EOFError):
            selected = DEFAULT_MODEL
            break

    if use_rich:
        console.print(f"\n[bold green]✓ Using: {selected}[/]\n")
    else:
        print(f"\nUsing: {selected}\n")
    return selected


@dataclass
class Agent:
    """Your personal AI agent. Create an instance and call .chat() to interact.

    Usage:
        agent = Agent()                          # loads config from .env
        response = agent.chat("list my files")   # agent takes action
        agent.interactive()                      # start vibrant interactive mode
    """

    config: Config = field(default_factory=lambda: Config.from_env())
    _engine: AgentEngine | None = field(default=None, init=False, repr=False)
    _voice_mode: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._setup_logging()
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
        self._engine = AgentEngine(config=self.config)

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.config.log_level, logging.INFO),
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    @property
    def tools(self) -> ToolRegistry:
        assert self._engine is not None
        return self._engine.tools

    def chat(self, message: str) -> str:
        assert self._engine is not None
        return self._engine.chat(message)

    def reset(self) -> None:
        if self._engine:
            self._engine.reset()

    def _get_voice_system(self):
        from cognition.voice import VoiceRecognition
        return VoiceRecognition()

    def interactive(self) -> None:
        """Start vibrant interactive mode with kaka-style UI."""
        console = Console()
        started_at = _time.time()
        history: list[dict] = []

        # ── Model selection (keep Buddy's 4-option flow) ──
        selected_model = select_model()
        if selected_model != self.config.model:
            if selected_model == "qwen2.5:3b":
                self.config.provider = "ollama"  # type: ignore
                self.config.model = selected_model
                self.config.base_url = "http://localhost:11434/v1"  # type: ignore
                self.config.api_key = "ollama"
                self.config._offline_active = True  # type: ignore
            else:
                self.config.model = selected_model
                # if previously offline, clear offline flag
                if getattr(self.config, "_offline_active", False):
                    self.config._offline_active = False  # type: ignore
                    # restore provider to gemini if was ollama
                    if getattr(self.config, "provider", "") == "ollama":
                        self.config.provider = "gemini"  # type: ignore
            self._engine = AgentEngine(config=self.config)

        def _tools_count() -> int:
            if self._engine and self._engine.tools:
                return len(self._engine.tools.list_tools())
            return 0

        def _render_frame() -> None:
            # Banner with Buddy branding but using ui.banner
            try:
                console.print(ui.banner(console, self.config.model, getattr(self.config, "provider", "gemini"), _tools_count()))
            except Exception:
                # fallback if ui.banner fails
                console.print(f"[bold cyan]Buddy.ai[/] — {self.config.model} • {_tools_count()} tools")
            console.print(
                ui.status_bar(
                    console,
                    getattr(self.config, "provider", "gemini"),
                    self.config.model,
                    _tools_count(),
                    bool(getattr(self.config, "privacy_mode", False)),
                    bool(getattr(self.config, "encrypt_data", False)),
                    started_at,
                )
            )

        _render_frame()
        ui.toast(console, "Engine ready • streaming on", "success")

        cmd_completions = [e.split("  —  ")[0] for e in ui.command_palette_entries()]
        for cmd, alias, _ in ui.COMMANDS:
            if alias:
                cmd_completions.append(alias)
        # Buddy-specific extras
        completer = FuzzyWordCompleter(cmd_completions + ["/theme", "/compact", "/offline", "/online", "/mode", "/model", "/voice", "/quit", "/clear", "/reset", "/stats"])
        prompt_style = Style.from_dict({"prompt": "bold ansicyan", "": "white"})
        prompt_session = PromptSession(
            history=InMemoryHistory(),
            completer=completer,
            style=prompt_style,
        )

        while True:
            try:
                raw = prompt_session.prompt("buddy> ")
                raw = str(raw or "").strip()
                if not raw:
                    continue

                low = raw.lower()

                if low in ("/quit", "/exit", "q", "quit", "exit"):
                    console.print(ui.exit_panel())
                    break

                if low in ("/help", "/h"):
                    console.print(ui.help_panel())
                    console.print(ui.divider())
                    continue

                if low in ("/tools", "/t"):
                    console.print(ui.categorized_tools_table(self.tools.list_tools()))
                    console.print(ui.divider())
                    continue

                if low in ("/history", "/hi"):
                    console.print(ui.history_table(history))
                    console.print(ui.divider())
                    continue

                if low in ("/theme",):
                    names = ["dark", "light", "neon"]
                    cur = ui._active_theme_name
                    nxt = names[(names.index(cur) + 1) % len(names)] if cur in names else "dark"
                    ui.set_theme(nxt)
                    console.print(f"Theme set to: {nxt}")
                    console.print(ui.divider())
                    continue

                if low in ("/mode", "/m"):
                    is_off = bool(getattr(self.config, "_offline_active", False)) or getattr(self.config, "provider", "") == "ollama"
                    mode = "OFFLINE (qwen2.5:3b @ Ollama)" if is_off else f"ONLINE ({getattr(self.config,'provider','gemini')}:{self.config.model})"
                    ui.info_box(console, f"Current mode: {mode}\nUse /offline or /online to switch", "info")
                    console.print(ui.divider())
                    continue

                if low in ("/offline", "/off"):
                    import os
                    snap = getattr(self.config, "_online_snapshot", None)
                    if not snap or "provider" not in snap:
                        snap = {"provider": getattr(self.config, "provider", "gemini"), "model": self.config.model, "base_url": getattr(self.config, "base_url", None), "api_key": self.config.api_key, "system_prompt": getattr(self.config, "system_prompt", ""), "max_tokens": self.config.max_tokens}
                        self.config._online_snapshot = snap  # type: ignore
                    off_model = os.getenv("OFFLINE_MODEL", "qwen2.5:3b")
                    off_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
                    self.config.provider = "ollama"  # type: ignore
                    self.config.model = off_model
                    self.config.base_url = off_base  # type: ignore
                    self.config.api_key = "ollama"
                    self.config.system_prompt = "You are a helpful offline assistant running locally on qwen2.5:3b Q4_K_M. Be concise, accurate, and helpful. No internet."
                    self.config.max_tokens = 512
                    self.config._offline_active = True  # type: ignore
                    try:
                        self._engine = AgentEngine(config=self.config)
                        ui.toast(console, f"Offline ✓ qwen2.5:3b via Ollama ({off_model})", "success")
                    except Exception as e:
                        ui.info_box(console, f"Offline switch failed: {e}", "error")
                    console.print(ui.divider())
                    continue

                if low in ("/online", "/on"):
                    snap = getattr(self.config, "_online_snapshot", None)
                    if snap and "provider" in snap:
                        self.config.provider = snap["provider"]  # type: ignore
                        self.config.model = snap["model"]
                        self.config.base_url = snap["base_url"]  # type: ignore
                        self.config.api_key = snap["api_key"]
                        if "system_prompt" in snap:
                            self.config.system_prompt = snap["system_prompt"]
                        if "max_tokens" in snap:
                            self.config.max_tokens = snap["max_tokens"]
                    else:
                        try:
                            from core.config import Config
                            fresh = Config.from_env()
                            if getattr(fresh, "provider", "gemini") != "ollama":
                                self.config.provider = fresh.provider  # type: ignore
                                self.config.model = fresh.model
                                self.config.base_url = fresh.base_url  # type: ignore
                                self.config.api_key = fresh.api_key
                                self.config.system_prompt = getattr(fresh, "system_prompt", "")
                                self.config.max_tokens = fresh.max_tokens
                        except Exception as e:
                            logging.debug(f"Config refresh failed: {e}")
                        self.config._offline_active = False  # type: ignore
                    try:
                        self._engine = AgentEngine(config=self.config)
                        ui.toast(console, f"Online ✓ {getattr(self.config,'provider','?')}:{self.config.model}", "success")
                    except Exception as e:
                        ui.info_box(console, f"Online switch failed: {e}", "error")
                    console.print(ui.divider())
                    continue

                if low in ("/compact",):
                    ui.toggle_compact()
                    ui.toast(console, "Compact mode toggled", "success")
                    console.print(ui.divider())
                    continue

                if low in ("/clear",):
                    console.clear()
                    _render_frame()
                    continue

                if low in ("/stats", "/s"):
                    console.print(ui.stats_panel(history, started_at, self.config.model, getattr(self.config, "provider", "gemini")))
                    console.print(ui.divider())
                    continue

                if low in ("/reset",):
                    self.reset()
                    history.clear()
                    ui.toast(console, "Conversation reset", "success")
                    console.print(ui.divider())
                    continue

                if low in ("/model",):
                    # re-run model selector
                    new_model = select_model()
                    if new_model != self.config.model:
                        if new_model == "qwen2.5:3b":
                            self.config.provider = "ollama"  # type: ignore
                            self.config.model = new_model
                            self.config.base_url = "http://localhost:11434/v1"  # type: ignore
                            self.config.api_key = "ollama"
                            self.config._offline_active = True  # type: ignore
                        else:
                            self.config.model = new_model
                            if getattr(self.config, "_offline_active", False):
                                self.config._offline_active = False  # type: ignore
                                if getattr(self.config, "provider", "") == "ollama":
                                    self.config.provider = "gemini"  # type: ignore
                        self._engine = AgentEngine(config=self.config)
                        ui.toast(console, f"Model switched to {new_model}", "success")
                    console.print(ui.divider())
                    continue

                if low == "voice" or low == "/voice":
                    voice = self._get_voice_system()
                    self._start_voice_mode(voice, True, console)
                    console.print(ui.divider())
                    continue

                # ── Normal chat turn ──
                console.print(ui.user_panel(raw))
                before_len = len(self._engine.messages) if self._engine else 0
                t0 = _time.perf_counter()
                try:
                    response = self.chat(raw)
                except Exception as e:
                    response = f"Error: {e}"
                dt_ms = int((_time.perf_counter() - t0) * 1000)

                tcs: list[dict] = []
                if self._engine and self._engine.messages:
                    for m in self._engine.messages[before_len:]:
                        if m.role == "assistant" and m.tool_calls:
                            tcs.extend(m.tool_calls)

                console.print(ui.agent_panel(response, tools_used=len(tcs), duration_ms=dt_ms))

                if tcs:
                    tp = ui.tool_panel(tcs, elapsed_ms=dt_ms)
                    if tp:
                        console.print(tp)

                history.append({
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "user": raw,
                    "agent": response,
                    "tools": len(tcs),
                    "ms": dt_ms,
                })
                console.print(ui.divider())

            except KeyboardInterrupt:
                ui.info_box(console, "Interrupted — type quit to exit", "warning")
            except EOFError:
                break
            except Exception as e:
                logging.exception("Unexpected error during session")
                ui.info_box(console, f"Error: {str(e)[:200]} — continuing", "error")

    def _start_voice_mode(self, voice, use_rich: bool, console=None) -> None:
        """Start voice conversation mode."""
        def agent_respond(text: str) -> str:
            return self.chat(text)

        def on_speak(text: str) -> None:
            voice.speak(text)

        if console:
            from rich.panel import Panel
            console.print(
                Panel(
                    "[bold yellow]🎤 VOICE MODE ACTIVATED[/]\n"
                    "Speak naturally — I'll listen until you pause\n"
                    "Say [bold]'quit voice'[/] to exit voice mode",
                    title="Voice Mode",
                    border_style="yellow",
                )
            )
        else:
            print("\n🎤 VOICE MODE ACTIVATED")

        try:
            voice.voice_chat(agent_respond, on_speak)
        except Exception as e:
            if console:
                ui.info_box(console, f"Voice error: {e}", "error")

        if console:
            from rich.panel import Panel
            console.print(
                Panel(
                    "[bold green]Back to text mode[/]",
                    title="Text Mode",
                    border_style="green",
                )
            )

    def add_tool(
        self,
        name: str,
        description: str,
        func: Any,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        if self._engine:
            self._engine.tools.register_function(name, description, func, parameters)
