"""Main Agent class — the primary interface for users."""
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
from prompt_toolkit.key_binding import KeyBindings

from .config import Config
from .engine import AgentEngine
from .tools import ToolRegistry
from . import ui

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


@dataclass
class Agent:
    config: Config = field(default_factory=lambda: Config.from_env())
    _engine: Any | None = field(default=None, init=False, repr=False)
    _voice_mode: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._setup_logging()
        errors = self.config.validate()
        if errors:
            raise ValueError(
                f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        from .builtins import register_built_in_tools

        reg = ToolRegistry()
        register_built_in_tools(reg)
        self._engine = AgentEngine(config=self.config, tools=reg)

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
        if self._engine is not None:
            self._engine.reset()

    def interactive(self) -> None:
        """Start interactive mode with prompt_toolkit."""
        console = Console()

        started_at = _time.time()
        history: list[dict] = []

        def _tools_count() -> int:
            if self._engine and self._engine.tools:
                return len(self._engine.tools.list_tools())
            return 0

        def _render_frame() -> None:
            console.print(ui.banner(console, DEFAULT_MODEL, self.config.provider, _tools_count()))
            console.print(
                ui.status_bar(
                    console,
                    self.config.provider,
                    DEFAULT_MODEL,
                    _tools_count(),
                    bool(getattr(self.config, "privacy_mode", False)),
                    bool(getattr(self.config, "encrypt_data", False)),
                    started_at,
                )
            )

        _render_frame()
        ui.toast(console, f"Engine ready • streaming on", "success")

        cmd_completions = [e.split("  —  ")[0] for e in ui.command_palette_entries()]
        for cmd, alias, _ in ui.COMMANDS:
            if alias:
                cmd_completions.append(alias)

        completer = FuzzyWordCompleter(cmd_completions + ["/theme", "/compact", "/offline", "/online", "/mode", "/model", "/voice", "/quit"])
        prompt_style = Style.from_dict({"prompt": "bold ansicyan", "": "white"})

        prompt_session = PromptSession(
            history=InMemoryHistory(),
            completer=completer,
            style=prompt_style,
        )

        while True:
            try:
                raw = prompt_session.prompt("kaka> ")
                raw = str(raw or "").strip()
                if not raw:
                    continue

                low = raw.lower()

                if low in ("/quit", "/exit", "q"):
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
                    is_off = bool(getattr(self.config, "_offline_active", False)) or self.config.provider == "ollama"
                    mode = "OFFLINE (qwen2.5:3b @ Ollama)" if is_off else f"ONLINE ({self.config.provider}:{self.config.model})"
                    ui.info_box(console, f"Current mode: {mode}\nUse /offline or /online to switch", "info")
                    console.print(ui.divider())
                    continue

                if low in ("/offline",):
                    self.config._offline_active = True
                    ui.toast(console, "Switched to offline mode", "success")
                    console.print(ui.divider())
                    continue

                if low in ("/online",):
                    self.config._offline_active = False
                    ui.toast(console, "Switched to online mode", "success")
                    console.print(ui.divider())
                    continue

                if low in ("/compact",):
                    ui.toggle_compact()
                    ui.toast(console, "Compact mode toggled", "success")
                    console.print(ui.divider())
                    continue

                if low in ("/reset",):
                    self.reset()
                    history.clear()
                    ui.toast(console, "Conversation reset", "success")
                    console.print(ui.divider())
                    continue

                if low.startswith("/model"):
                    parts = raw.split(maxsplit=1)
                    available = [
                        "nvidia/nemotron-3-super-120b-a12b:free",
                        "google/gemma-4-31b-it:free",
                        "nvidia/nemotron-3.5-lightning:free",
                        "inclusionai/ling-3.0-flash-fin:free",
                        "cohere/north-mini-code:free",
                        "z-ai/glm-5.2:free",
                        "minimax/minimax-m3:free",
                    ]
                    if len(parts) == 1:
                        cur = self.config.model
                        console.print(f"[bold]Current model:[/bold] {cur}")
                        console.print("[bold]Available models:[/bold]")
                        for i, m in enumerate(available, 1):
                            marker = " [green]<-- current[/green]" if m == cur else ""
                            console.print(f"  {i}. {m}{marker}")
                        console.print("\nUsage: /model <name or number>")
                        console.print(ui.divider())
                        continue
                    selection = parts[1].strip()
                    if selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(available):
                            new_model = available[idx]
                        else:
                            ui.info_box(console, f"Invalid number. Choose 1-{len(available)}", "warning")
                            console.print(ui.divider())
                            continue
                    else:
                        new_model = selection
                    old_model = self.config.model
                    self.config.model = new_model
                    self._engine.config.model = new_model
                    ui.toast(console, f"Model: {old_model} -> {new_model}", "success")
                    console.print(ui.divider())
                    continue

                # ── Normal chat turn ──────────────────────────────────────
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
