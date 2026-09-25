#!/usr/bin/env python3
"""CLI entry point for Kaka.ai — vibrant, structured terminal experience."""
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
        console.print(f"\n[dim]Total: {len(agent.tools.list_tools())} tools  •  use [bold]kaka \"your task\"[/] to run[/]\n")
    except ImportError:
        tools = agent.tools.list_tools()
        print(f"Available tools ({len(tools)}):\n")
        for t in tools:
            print(f"  {t['name']:22s} — {t['description']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kaka",
        description="Kaka.ai — Your autonomous AI assistant for the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n  kaka                          interactive chat\n  kaka \"summarize README.md\"      single task\n  kaka --tools                  browse capabilities\n  kaka --serve --port 8900      start API server\n",
    )
    parser.add_argument("message", nargs="*", help="Message to send (if omitted, starts interactive mode)")
    parser.add_argument("--model", "-m", default=None, help="Override model name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose tool logging")
    parser.add_argument("--reset", action="store_true", help="Reset conversation history")
    parser.add_argument("--tools", action="store_true", help="List available tools (categorized)")
    parser.add_argument("--serve", action="store_true", help="Run as HTTP API server (default port 8900)")
    parser.add_argument("--port", type=int, default=8900, help="Port for --serve mode")
    parser.add_argument("--config", "-c", default=None, help="Path to .env config file")
    args = parser.parse_args()

    config = Config.from_env(args.config)
    if args.model:
        config.model = args.model
    if args.verbose:
        config.verbose = True

    if config.encrypt_data and not config.data_passphrase and not args.serve:
        import getpass
        config.data_passphrase = getpass.getpass("Data encryption passphrase (unlocks memories/conversations): ")

    try:
        agent = Agent(config=config)
    except ValueError as e:
        try:
            from rich.console import Console
            from rich.panel import Panel
            Console().print(Panel(f"[bold red]Configuration error[/]\n{e}", border_style="red", title="✖  Kaka.ai"))
        except ImportError:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.serve:
        import server
        sys.argv = ["kaka-server", "--port", str(args.port)]
        server.main()
        return

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

            # Live streaming panel
            with Live(
                Panel(Text("◐  Thinking…", style="dim cyan"), title="[cyan]Kaka.ai is thinking[/]", border_style="cyan", box=ROUNDED),
                console=console, refresh_per_second=14, transient=False
            ) as live:
                def _on_delta(s: str) -> None:
                    nonlocal streamed_text
                    streamed_text += s
                    is_streaming[0] = True
                    live.update(Panel(Markdown(streamed_text + " ▌"), title="[bold #00D9FF]🤖  Kaka.ai  [dim]• streaming[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
                engine = getattr(agent, "_engine", None)
                if engine is not None:
                    engine.stream_callback = _on_delta
                t0 = time.perf_counter()
                response = agent.chat(query)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                if is_streaming[0]:
                    live.update(Panel(Markdown(streamed_text or response), title="[bold #00D9FF]🤖  Kaka.ai[/]", subtitle=f"[dim]◷ {dt_ms/1000:.1f}s[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
                else:
                    live.update(Panel(Markdown(response), title="[bold #00D9FF]🤖  Kaka.ai[/]", subtitle=f"[dim]◷ {dt_ms/1000:.1f}s[/]", border_style="#00D9FF", box=ROUNDED, padding=(0, 1)))
            # Tool summary if any
            try:
                from core.ui import tool_panel
                # collect last turn tool calls from engine messages
                msgs = getattr(agent, "_engine", None)
                if msgs and msgs.messages:
                    # find last user message index, collect assistant tool_calls after it
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
