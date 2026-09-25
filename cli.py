#!/usr/bin/env python3
"""CLI entry point for Buddy.ai — vibrant, structured terminal experience."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import Agent
from core.config import Config


def _print_tools(agent: Agent) -> None:
    try:
        from rich.console import Console
        from core.ui import categorized_tools_table
        console = Console()
        console.print(categorized_tools_table(agent.tools.list_tools()))
        console.print(f"\n[dim]Total: {len(agent.tools.list_tools())} tools  •  use [bold]buddy \"your task\"[/] to run[/]\n")
    except ImportError:
        tools = agent.tools.list_tools()
        print(f"Available tools ({len(tools)}):\n")
        for t in tools:
            print(f"  {t['name']:22s} — {t['description']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="buddy",
        description="Buddy.ai — Your autonomous AI assistant for the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  buddy                          interactive chat\n  buddy \"summarize README.md\"      single task\n  buddy --tools                  browse capabilities\n  buddy --offline                start in offline mode (qwen2.5:3b)\n",
    )
    parser.add_argument("message", nargs="*", help="Message to send (if omitted, starts interactive mode)")
    parser.add_argument("--model", "-m", default=None, help="Override model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose tool logging")
    parser.add_argument("--reset", action="store_true", help="Reset conversation history")
    parser.add_argument("--tools", action="store_true", help="List available tools (categorized)")
    parser.add_argument("--offline", action="store_true", help="Start in offline mode (qwen2.5:3b via Ollama)")
    parser.add_argument("--online", action="store_true", help="Force online mode")
    parser.add_argument("--config", "-c", default=None, help="Path to .env config file")
    args = parser.parse_args()

    config = Config.from_env(args.config)
    if args.model:
        config.model = args.model
    if args.verbose:
        config.verbose = True

    # Offline/online toggle
    if args.offline:
        config.provider = "ollama"
        config.model = "qwen2.5:3b"
        config._offline_active = True
    if args.online:
        config._offline_active = False

    if getattr(config, "encrypt_data", False) and not getattr(config, "data_passphrase", None):
        import getpass
        try:
            config.data_passphrase = getpass.getpass("Data encryption passphrase (unlocks memories/conversations): ")
        except Exception:
            pass

    try:
        agent = Agent(config=config)
    except ValueError as e:
        try:
            from rich.console import Console
            from rich.panel import Panel
            Console().print(Panel(f"[bold red]Configuration error[/]\n{e}", border_style="red", title="✖  Buddy.ai"))
        except ImportError:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.tools:
        _print_tools(agent)
        return

    if args.reset:
        agent.reset()
        try:
            from rich.console import Console
            from rich.panel import Panel
            Console().print(Panel("[green]✓ Conversation history cleared.[/]", border_style="green", title="↺  Reset"))
        except ImportError:
            print("Conversation history cleared.")
        return

    if args.message:
        query = " ".join(args.message)
        # ── Single-shot with vibrant output ──
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.markdown import Markdown
            from rich.live import Live
            from rich.text import Text
            from rich.box import ROUNDED
            console = Console()
            has_rich = True
        except ImportError:
            has_rich = False

        if has_rich:
            console.print(Panel(Text(query, style="white"), title="[bold #5B8DEF]👤  You[/]", border_style="#5B8DEF", box=ROUNDED, padding=(0, 1)))
            streamed_text = ""
            is_streaming = [False]

            with Live(
                Panel(Text("◐  Thinking…", style="dim cyan"), title="[cyan]Buddy.ai is thinking[/]", border_style="cyan", box=ROUNDED),
                console=console, refresh_per_second=14, transient=False
            ) as live:
                def _on_delta(s: str) -> None:
                    nonlocal streamed_text
                    streamed_text += s
                    is_streaming[0] = True
                    live.update(Panel(Markdown(streamed_text + " ▌"), title="[bold #00D9FF]🤖  Buddy.ai  [dim]• streaming[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
                engine = getattr(agent, "_engine", None)
                if engine is not None:
                    engine.stream_callback = _on_delta
                t0 = time.perf_counter()
                response = agent.chat(query)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                if is_streaming[0]:
                    live.update(Panel(Markdown(streamed_text or response), title="[bold #00D9FF]🤖  Buddy.ai[/]", subtitle=f"[dim]◷ {dt_ms/1000:.1f}s[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
                else:
                    live.update(Panel(Markdown(response), title="[bold #00D9FF]🤖  Buddy.ai[/]", subtitle=f"[dim]◷ {dt_ms/1000:.1f}s[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
            try:
                from core.ui import tool_panel
                msgs = getattr(agent, "_engine", None)
                if msgs and msgs.messages:
                    last_user_idx = max((i for i, m in enumerate(msgs.messages) if m.role == "user"), default=0)
                    tcs = []
                    for m in msgs.messages[last_user_idx:]:
                        if m.role == "assistant" and m.tool_calls:
                            tcs.extend(m.tool_calls)
                    tp = tool_panel(tcs)
                    if tp:
                        console.print(tp)
            except Exception:
                pass
        else:
            streamed = [False]
            def _on_delta2(s: str) -> None:
                streamed[0] = True
                print(s, end="", flush=True)
            engine = getattr(agent, "_engine", None)
            if engine is not None:
                engine.stream_callback = _on_delta2
            response = agent.chat(query)
            if streamed[0]:
                print()
            else:
                print(response)
    else:
        agent.interactive()


if __name__ == "__main__":
    main()
