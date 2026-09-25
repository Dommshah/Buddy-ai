"""Buddy.ai — Modern Design System.

Clean, vibrant, categorised terminal UI with:
  • Theme variants (dark / light / neon)
  • RGB-animated banner
  • Floating input bar with keyboard hints
  • Syntax-highlighted code blocks
  • Toast notifications
  • Command palette
  • Progress spinners
  • Compact mode
  • Integrated history panel
"""
from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown
from rich.syntax import Syntax
from rich.box import ROUNDED, HEAVY, MINIMAL, SIMPLE, ROUNDED
from rich.rule import Rule
from rich.columns import Columns
from rich.align import Align
from rich.spinner import Spinner
from rich.theme import Theme as RichTheme


# ──────────────────────────────────────────────────────────────
#  1.  THEMES
# ──────────────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "primary":    "#00D9FF",   # cyan
        "secondary":  "#B967FF",   # purple
        "user":       "#5B8DEF",   # blue
        "success":    "#00E676",   # green
        "warning":    "#FFCA28",   # amber
        "error":      "#FF5252",   # red
        "tool":       "#FFB74D",   # orange
        "muted":      "dim white",
        "dim":        "bright_black",
        "text":       "white",
        "bg":         "default",
        "banner1":    "#00D9FF",
        "banner2":    "#B967FF",
        "banner3":    "#00E676",
    },
    "light": {
        "primary":    "#0077B6",
        "secondary":  "#7B2D8E",
        "user":       "#2563EB",
        "success":    "#16A34A",
        "warning":    "#D97706",
        "error":      "#DC2626",
        "tool":       "#C2410C",
        "muted":      "dim black",
        "dim":        "bright_black",
        "text":       "black",
        "bg":         "default",
        "banner1":    "#0077B6",
        "banner2":    "#7B2D8E",
        "banner3":    "#16A34A",
    },
    "neon": {
        "primary":    "#FF00FF",   # magenta
        "secondary":  "#00FFFF",   # cyan
        "user":       "#FFFF00",   # yellow
        "success":    "#39FF14",   # neon green
        "warning":    "#FF6600",   # neon orange
        "error":      "#FF0033",   # neon red
        "tool":       "#FF69B4",   # hot pink
        "muted":      "dim white",
        "dim":        "bright_black",
        "text":       "white",
        "bg":         "default",
        "banner1":    "#FF00FF",
        "banner2":    "#00FFFF",
        "banner3":    "#39FF14",
    },
}

_active_theme_name: str = "dark"
_active_theme: dict[str, str] = THEMES["dark"]
compact_mode: bool = False


def set_theme(name: str) -> dict[str, str]:
    global _active_theme_name, _active_theme
    if name in THEMES:
        _active_theme_name = name
        _active_theme = THEMES[name]
    return _active_theme


def get_theme() -> dict[str, str]:
    return _active_theme


def toggle_compact() -> bool:
    global compact_mode
    compact_mode = not compact_mode
    return compact_mode


# ──────────────────────────────────────────────────────────────
#  2.  RGB ANIMATED BANNER
# ──────────────────────────────────────────────────────────────

def _thumb_text(text: str, colors: list[str], width: int) -> Text:
    """Return Text with characters cycling through RGB colors."""
    t = Text()
    for i, ch in enumerate(text):
        t.append(ch, style=f"bold {colors[i % len(colors)]}")
    return t


BANNER_ART = r"""
 ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗   ██╗       █████╗ ██╗
 ██╔══██╗██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝      ██╔══██╗██║
 ██████╔╝██║   ██║██║  ██║██║  ██║ ╚████╔╝ █████╗███████║██║
 ██╔══██╗██║   ██║██║  ██║██║  ██║  ╚██╔╝  ╚════╝██╔══██║██║
 ██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║        ██║  ██║██║
 ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝        ╚═╝  ╚═╝╚═╝
"""


def banner(console: Console, model: str, provider: str, tools_count: int) -> Panel:
    """ASCII-art logo banner with RGB-cycling glow — vibrant, clean."""
    c = get_theme()
    cols = [c["banner1"], c["banner2"], c["banner3"]]

    # ASCII art, each line cycles through the RGB palette
    art = _thumb_text("\n".join(BANNER_ART.strip("\n").split("\n")), cols, console.width or 80)

    # Subtitle line
    sub = Text()
    sub.append("◉ ", style=f"bold {c['primary']}")
    sub.append(provider, style=f"bold {c['text']}")
    sub.append("  ›  ", style=c["dim"])
    sub.append(model.split("/")[-1].replace(":free", ""), style=f"bold {c['secondary']}")
    sub.append("  ›  ", style=c["dim"])
    sub.append(f"{tools_count} tools", style=f"bold {c['tool']}")

    body = Text()
    body.append_text(art)
    body.append("\n\n")
    body.append("   ", style=c["dim"])
    body.append_text(sub)

    return Panel(
        Align.center(body),
        box=HEAVY,
        border_style=f"bold {c['primary']}",
        padding=(1, 2),
        title=f"[bold {c['secondary']}]◉  Buddy.ai  v2.1[/]",
        subtitle=f"[dim {c['dim']}]type /help • Tab for commands[/]",
    )


# ──────────────────────────────────────────────────────────────
#  3.  STATUS BAR
# ──────────────────────────────────────────────────────────────

def status_bar(console: Console, provider: str, model: str, tools_count: int,
               privacy: bool, encrypted: bool, started_at: float) -> Panel:
    c = get_theme()
    elapsed = int(time.time() - started_at)
    mins, secs = divmod(elapsed, 60)

    t = Text()
    t.append(" ◉ ", style=c["primary"])
    t.append(provider, style=f"bold {c['text']}")
    t.append("  ", style="default")
    t.append("⬢ ", style=c["secondary"])
    t.append(model.split("/")[-1].replace(":free", ""), style=c["text"])
    t.append("  ", style="default")
    t.append("⚙ ", style=c["tool"])
    t.append(str(tools_count), style=f"bold {c['tool']}")
    t.append("  ", style="default")
    if privacy:
        t.append("🔒 private ", style=c["success"])
    if encrypted:
        t.append("🔐 sealed ", style=c["success"])
    t.append("◷ ", style=c["warning"])
    t.append(f"{mins:02d}:{secs:02d}", style=f"bold {c['warning']}")

    return Panel(t, box=MINIMAL, padding=(0, 1), border_style=c["dim"])


# ──────────────────────────────────────────────────────────────
#  4.  INPUT BAR  (floating prompt)
# ──────────────────────────────────────────────────────────────

def input_bar(console: Console, prompt_text: str = "❯") -> Text:
    """The styled input prompt — rendered by prompt_toolkit, this sets color."""
    c = get_theme()
    return Text(f" {prompt_text} ", style=f"bold {c['primary']}")


def keyboard_hints() -> Panel:
    """Bottom hint bar with keybindings."""
    c = get_theme()
    hints = [
        ("Tab", "commands"),
        ("↑↓", "history"),
        ("Ctrl+K", "palette"),
        ("Ctrl+L", "clear"),
        ("Ctrl+D", "quit"),
    ]
    t = Text()
    for i, (key, action) in enumerate(hints):
        if i > 0:
            t.append("  │  ", style=c["dim"])
        t.append(key, style=f"bold {c['primary']}")
        t.append(f" {action}", style=c["muted"])
    return Panel(Align.center(t), box=MINIMAL, padding=(0, 1), border_style=c["dim"])


# ──────────────────────────────────────────────────────────────
#  5.  USER / AGENT / TOOL PANELS  (core I/O blocks)
# ──────────────────────────────────────────────────────────────

def user_panel(text: str) -> Panel:
    c = get_theme()
    return Panel(
        Text(text, style=c["text"]),
        title=f"[bold {c['user']}]👤  You[/]",
        border_style=c["user"],
        box=ROUNDED,
        padding=(0, 1),
    )


def agent_panel(text: str, tools_used: int = 0, duration_ms: int = 0) -> Panel:
    c = get_theme()
    subtitle_parts = []
    if tools_used:
        subtitle_parts.append(f"⚙ {tools_used} tool{'s' if tools_used != 1 else ''}")
    if duration_ms:
        subtitle_parts.append(f"◷ {duration_ms / 1000:.1f}s")
    subtitle = f"[dim]{'  •  '.join(subtitle_parts)}[/]" if subtitle_parts else ""

    # Render markdown → syntax-highlighted code blocks, bold, lists
    if text.strip():
        content = RichMarkdown(text)
    else:
        content = Text("(no response)", style=c["muted"])

    return Panel(
        content,
        title=f"[bold {c['primary']}]🤖  Buddy.ai[/]",
        subtitle=subtitle,
        border_style=c["primary"],
        box=ROUNDED,
        padding=(0, 1),
    )


def streaming_panel(text: str, is_streaming: bool = True) -> Panel:
    """Panel used during streaming — shows blinking cursor."""
    c = get_theme()
    cursor = " ▌" if is_streaming else ""
    label = "streaming" if is_streaming else "done"

    if text.strip():
        content = RichMarkdown(text + cursor)
    else:
        content = Text("◐  Thinking…", style=f"dim {c['primary']}")

    return Panel(
        content,
        title=f"[bold {c['primary']}]🤖  Buddy.ai[/]  [dim {c['dim']}]{label}[/]",
        border_style=c["primary"],
        box=ROUNDED,
        padding=(0, 1),
    )


def thinking_panel() -> Panel:
    c = get_theme()
    return Panel(
        Text("  ◐  Thinking…", style=f"bold {c['primary']}"),
        border_style=c["primary"],
        box=ROUNDED,
        padding=(0, 1),
    )


def thinking_signal(console: Console) -> None:
    """A single boxed line — nothing but the thinking state (no extra info)."""
    c = get_theme()
    console.print(
        Panel(
            Align.center(Text("◐ thinking…", style=f"bold {c['primary']}")),
            box=ROUNDED,
            border_style=c["dim"],
            padding=(0, 1),
        )
    )


def info_box(console: Console, message: str, kind: str = "info") -> None:
    """A boxed one-liner for loose status info (aligned, structured)."""
    c = get_theme()
    icons = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}
    colors = {"info": c["primary"], "success": c["success"], "warning": c["warning"], "error": c["error"]}
    color = colors.get(kind, c["primary"])
    console.print(
        Panel(
            Align.center(Text(f" {icons.get(kind, '●')}  {message}", style=f"bold {color}")),
            box=ROUNDED,
            border_style=c["dim"],
            padding=(0, 1),
        )
    )


def stream_frame(console: Console, *, status: str = "thinking…", elapsed: str | None = None,
                 words: int | None = None, tools: int | None = None, close: bool = False) -> None:
    """Single static section boundary for the live response.

    Open frame shows ONLY the thinking state; close frame shows ONLY
    the response details (time, words, tools). Printed once each —
    no cursor control, no Live, no escape-code chatter.
    """
    from rich.cells import cell_len
    c = get_theme()
    width = max((console.width or 80) - 2, 16)
    line = Text()
    corner = "╰" if close else "╭"
    line.append(corner, style=f"bold {c['primary']}")

    if not close:
        title = f" ◐ {status}"
        line.append(title, style=f"bold {c['primary']}")
        remain = max(width - cell_len(title), 0)
        line.append("─" * remain, style=c["dim"])
    else:
        sub = " "
        if elapsed is not None:
            sub += f"◷ {elapsed}"
        if words is not None:
            sub += f"  ·  {words} words"
        if tools:
            sub += f"  ·  {tools} tool{'s' if tools != 1 else ''}"
        sub += "  "
        line.append(sub, style=c["muted"])
        remain = max(width - cell_len(sub), 0)
        line.append("─" * remain, style=c["dim"])

    line.append("╯" if close else "╮", style=f"bold {c['primary']}")
    console.print(line)


def tool_panel(tool_calls: list[dict[str, Any]], elapsed_ms: int | None = None) -> Panel | None:
    if not tool_calls:
        return None
    c = get_theme()
    tbl = Table(show_header=True, header_style=f"bold {c['tool']}", box=SIMPLE, padding=(0, 1), expand=True)
    tbl.add_column("#", style="dim", width=3, justify="right")
    tbl.add_column("Tool", style=f"bold {c['tool']}", width=20)
    tbl.add_column("Arguments", style=c["text"], overflow="fold")
    for i, tc in enumerate(tool_calls, 1):
        name = tc.get("function", {}).get("name", "?") if isinstance(tc, dict) else str(tc)
        args = tc.get("function", {}).get("arguments", "") if isinstance(tc, dict) else ""
        if isinstance(args, str) and len(args) > 100:
            args = args[:100] + "…"
        tbl.add_row(str(i), name, args)
    subtitle = f"[dim {c['dim']}]{len(tool_calls)} call{'s' if len(tool_calls) != 1 else ''}[/]"
    if elapsed_ms:
        subtitle += f"  [dim {c['dim']}]{elapsed_ms}ms[/]"
    return Panel(tbl, title=f"[bold {c['tool']}]⚙  Tool Calls[/]", subtitle=subtitle, border_style=c["tool"], box=ROUNDED, padding=(0, 1))


# ──────────────────────────────────────────────────────────────
#  6.  PROGRESS SPINNER
# ──────────────────────────────────────────────────────────────

def spinner(console: Console, message: str = "Working") -> Spinner:
    c = get_theme()
    return Spinner("dots", text=f" {message}…", style=c["primary"])


# ──────────────────────────────────────────────────────────────
#  7.  TOAST NOTIFICATIONS
# ──────────────────────────────────────────────────────────────

def toast(console: Console, message: str, kind: str = "info", duration: float = 2.0) -> None:
    """Brief notification that auto-clears."""
    c = get_theme()
    icons = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗", "tool": "⚙"}
    colors = {"info": c["primary"], "success": c["success"], "warning": c["warning"], "error": c["error"], "tool": c["tool"]}
    icon = icons.get(kind, "●")
    color = colors.get(kind, c["primary"])
    panel = Panel(
        Text(f" {icon}  {message}", style=f"bold {color}"),
        box=ROUNDED,
        border_style=color,
        padding=(0, 1),
    )
    console.print(panel)


# ──────────────────────────────────────────────────────────────
#  8.  COMMAND PALETTE
# ──────────────────────────────────────────────────────────────

COMMANDS = [
    ("/help",       "h",   "Show help & commands"),
    ("/tools",      "t",   "Browse tools by category"),
    ("/history",    "hi",  "Conversation history"),
    ("/clear",      "c",   "Clear screen"),
    ("/model",      "m",   "Switch model"),
    ("/stats",      "s",   "Session statistics"),
    ("/theme",      "",    "Switch theme (dark/light/neon)"),
    ("/compact",    "",    "Toggle compact mode"),
    ("/export",     "",    "Export history to file"),
    ("/reset",      "",    "Clear conversation memory"),
    ("/voice",      "",    "Voice mode"),
    ("quit",        "",    "Exit Buddy.ai"),
]


def help_panel() -> Panel:
    c = get_theme()
    t = Table(show_header=True, header_style=f"bold {c['primary']}", box=MINIMAL, padding=(0, 1))
    t.add_column("Command", style=f"bold {c['secondary']}", width=14)
    t.add_column("Alias", style=f"dim {c['dim']}", width=6)
    t.add_column("Description", style=c["text"])
    for cmd, alias, desc in COMMANDS:
        t.add_row(cmd, alias, desc)
    return Panel(t, title=f"[bold {c['primary']}]📖  Commands[/]", border_style=c["primary"], box=ROUNDED, padding=(0, 1))


def command_palette_entries() -> list[str]:
    """Fuzzy-searchable list for Ctrl+K palette."""
    entries = []
    for cmd, alias, desc in COMMANDS:
        entries.append(f"{cmd}  —  {desc}")
    return entries


# ──────────────────────────────────────────────────────────────
#  9.  TOOLS TABLE  (categorised, single flat table)
# ──────────────────────────────────────────────────────────────

CATEGORY_MAP = {
    "git_":       "Git",
    "sqlite":     "Database",
    "remember_semantic": "Memory", "search_semantic": "Memory",
    "save_memory": "Memory", "recall_memory": "Memory",
    "hf_":        "AI Models",
    "pdf_read":   "Documents", "docx_read": "Documents", "csv_analyze": "Documents",
    "analyze_image": "Web & Vision", "browse_page": "Web & Vision",
    "scrape_url": "Web & Vision", "fetch_url": "Web & Vision", "web_search": "Web & Vision",
    "calculate":  "Data", "json_query": "Data", "data_analyze": "Data",
    "pattern_detect": "Data", "predict": "Data", "verify": "Data",
    "code_analyze": "Code", "code_generate": "Code",
    "security_scan": "Code", "security_audit": "Code",
    "content_create": "Content", "creative_idea": "Content", "creative_writing_prompt": "Content",
    "voice_transcribe": "Voice", "voice_listen": "Voice", "voice_speak": "Voice",
    "reason":     "Cognition", "autonomy_plan": "Cognition", "autonomy_decide": "Cognition",
}


def categorized_tools_table(tools: list[dict[str, str]]) -> Panel:
    c = get_theme()
    cats: dict[str, list[dict]] = {}
    for t in tools:
        name = t["name"]
        cat = "System"
        for prefix, cname in CATEGORY_MAP.items():
            if name == prefix or name.startswith(prefix):
                cat = cname
                break
        cats.setdefault(cat, []).append(t)

    tbl = Table(show_header=True, header_style=f"bold {c['primary']}", box=ROUNDED, expand=True, show_lines=False)
    tbl.add_column("Category", style=f"bold {c['secondary']}", width=14)
    tbl.add_column("Tool", style=f"bold {c['tool']}", width=22)
    tbl.add_column("Description", style=c["text"], overflow="fold")

    for cat in sorted(cats.keys()):
        sorted_tools = sorted(cats[cat], key=lambda x: x["name"])
        for j, tool in enumerate(sorted_tools):
            label = f"{cat}  ({len(cats[cat])})" if j == 0 else ""
            tbl.add_row(label, tool["name"], tool["description"][:85])

    return Panel(tbl, title=f"[bold {c['primary']}]🧰  Tools — {len(tools)}[/]  [dim {c['dim']}]{len(cats)} categories[/]", border_style=c["primary"], box=ROUNDED, padding=(0, 1))


# ──────────────────────────────────────────────────────────────
#  10.  HISTORY TABLE  (integrated in main layout)
# ──────────────────────────────────────────────────────────────

def history_table(history: list[dict[str, Any]]) -> Panel:
    c = get_theme()
    if not history:
        return Panel(Text("No history yet — start chatting!", style=c["muted"]),
                     title=f"[bold {c['primary']}]📜  History[/]", border_style=c["dim"], box=ROUNDED)

    tbl = Table(show_header=True, header_style=f"bold {c['primary']}", box=SIMPLE, expand=True)
    tbl.add_column("#", style="dim", width=3, justify="right")
    tbl.add_column("Time", style=c["muted"], width=8)
    tbl.add_column("You", style=c["user"], overflow="fold", ratio=2)
    tbl.add_column("Buddy.ai", style=c["text"], overflow="fold", ratio=3)
    tbl.add_column("⚙", style=c["tool"], width=4, justify="center")
    for i, h in enumerate(history[-20:], 1):
        t = h.get("time", "")[11:19] if len(h.get("time", "")) > 10 else h.get("time", "")
        you = h.get("user", "")[:80] + ("…" if len(h.get("user", "")) > 80 else "")
        ai = h.get("agent", "")[:90].replace("\n", " ") + ("…" if len(h.get("agent", "")) > 90 else "")
        tbl.add_row(str(i), t, you, ai, str(h.get("tools", 0) or 0))
    return Panel(tbl, title=f"[bold {c['primary']}]📜  History — last {min(len(history), 20)}/{len(history)}[/]", border_style=c["primary"], box=ROUNDED, padding=(0, 1))


def inline_history_turn(turn: dict) -> Panel:
    """Compact single-turn history for the scrollable area."""
    c = get_theme()
    t = Text()
    t.append(f"👤 {turn.get('user', '')[:100]}", style=c["user"])
    t.append("\n")
    response_preview = turn.get("agent", "")[:200].replace("\n", " ")
    t.append(f"🤖 {response_preview}", style=c["text"])
    if turn.get("tools"):
        t.append(f"  ⚙ {turn['tools']}", style=c["tool"])
    return Panel(t, box=MINIMAL, border_style=c["dim"], padding=(0, 1))


# ──────────────────────────────────────────────────────────────
#  11.  STATS PANEL
# ──────────────────────────────────────────────────────────────

def stats_panel(history: list[dict], started_at: float, model: str, provider: str) -> Panel:
    c = get_theme()
    total = len(history)
    elapsed = int(time.time() - started_at)
    tool_total = sum(h.get("tools", 0) for h in history)
    avg_ms = int(sum(h.get("ms", 0) for h in history) / total) if total else 0

    tbl = Table(show_header=False, box=SIMPLE, padding=(0, 2))
    tbl.add_column("K", style=f"bold {c['muted']}", width=16)
    tbl.add_column("V", style=f"bold {c['text']}")
    tbl.add_row("Session time", f"{elapsed // 60:02d}:{elapsed % 60:02d}")
    tbl.add_row("Messages", str(total))
    tbl.add_row("Tool calls", str(tool_total))
    tbl.add_row("Avg response", f"{avg_ms / 1000:.1f}s" if avg_ms else "—")
    tbl.add_row("Model", model.split("/")[-1].replace(":free", ""))
    tbl.add_row("Provider", provider)
    tbl.add_row("Theme", _active_theme_name)

    return Panel(tbl, title=f"[bold {c['secondary']}]📊  Session Stats[/]", border_style=c["secondary"], box=ROUNDED, padding=(0, 1))


# ──────────────────────────────────────────────────────────────
#  12.  DIVIDERS & SEPARATORS
# ──────────────────────────────────────────────────────────────

def divider(label: str = "") -> Rule:
    c = get_theme()
    return Rule(label, style=c["dim"])


def section_header(title: str) -> Text:
    """A section divider with title."""
    c = get_theme()
    t = Text()
    t.append(f"\n  ── {title} ", style=f"bold {c['primary']}")
    t.append("─" * 40, style=c["dim"])
    return t


# ──────────────────────────────────────────────────────────────
#  13.  COMPACT vs NORMAL display helpers
# ──────────────────────────────────────────────────────────────

def pad_amount() -> tuple[int, int]:
    return (0, 0) if compact_mode else (0, 1)


# ──────────────────────────────────────────────────────────────
#  14.  EXIT PANEL
# ──────────────────────────────────────────────────────────────

def exit_panel() -> Panel:
    c = get_theme()
    return Panel(
        Align.center(Text("Thanks for using Buddy.ai — see you next time! 👋", style=f"bold {c['primary']}")),
        box=ROUNDED,
        border_style=c["primary"],
        padding=(1, 2),
    )
