"""SQLite database query tools for the Kaka.ai agent."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from core.tools import Tool

_MAX_ROWS = 100
_MAX_CELL = 300


def _sqlite_query(db_path: str, sql: str, allow_write: bool = False) -> str:
    """Execute SQL against a SQLite database. Read-only unless allow_write."""
    path = Path(db_path).expanduser()
    if not path.exists():
        return f"Error: database not found: {path}"

    sql_stripped = sql.strip().rstrip(";")
    first_word = sql_stripped.split()[0].upper() if sql_stripped else ""
    is_write = first_word in {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE", "ATTACH", "DETACH"}
    if is_write and not allow_write:
        return (
            f"Blocked: '{first_word}' is a write operation. "
            "Pass allow_write=true only when the user explicitly asked for changes."
        )

    try:
        if allow_write:
            conn = sqlite3.connect(str(path), timeout=10)
        else:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql_stripped)

        if cur.description is None:
            conn.commit()
            affected = cur.rowcount
            conn.close()
            return f"OK — {affected} row(s) affected."

        rows = cur.fetchmany(_MAX_ROWS + 1)
        more = len(rows) > _MAX_ROWS
        rows = rows[:_MAX_ROWS]
        cols = [d[0] for d in cur.description]
        conn.close()

        lines = [" | ".join(cols)]
        lines.append("-" * min(120, max(len(l) for l in lines)))
        for r in rows:
            cells = [str(v)[:_MAX_CELL] for v in r]
            lines.append(" | ".join(cells))
        if more:
            lines.append(f"... ({_MAX_ROWS} row limit; refine your query)")
        return "\n".join(lines)
    except sqlite3.Error as e:
        return f"SQL error: {e}"
    finally:
        if "conn" in dir():
            try:
                conn.close()
            except Exception:
                pass


def _sqlite_tables(db_path: str) -> str:
    path = Path(db_path).expanduser()
    if not path.exists():
        return f"Error: database not found: {path}"
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )]
        out = []
        for t in tables:
            cols = [f"{r[1]} {r[2]}" for r in conn.execute(f"PRAGMA table_info('{t}')")]
            n = conn.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
            out.append(f"{t} ({n} rows)\n  - " + "\n  - ".join(cols))
        conn.close()
        return "\n\n".join(out) or "(no tables)"
    except sqlite3.Error as e:
        return f"SQL error: {e}"


def register(registry: Any) -> None:
    registry.register(Tool(
        name="sqlite_query",
        description="Run SQL against a SQLite database file. Read-only by default; writes require allow_write=true.",
        parameters={
            "type": "object",
            "properties": {
                "db_path": {"type": "string", "description": "Path to .db/.sqlite file"},
                "sql": {"type": "string", "description": "SQL statement to execute"},
                "allow_write": {"type": "boolean", "description": "Permit INSERT/UPDATE/DELETE/DDL (default false)"},
            },
            "required": ["db_path", "sql"],
        },
        execute=_sqlite_query,
    ))
    registry.register(Tool(
        name="sqlite_tables",
        description="List tables, columns, and row counts of a SQLite database (schema introspection).",
        parameters={
            "type": "object",
            "properties": {
                "db_path": {"type": "string", "description": "Path to .db/.sqlite file"},
            },
            "required": ["db_path"],
        },
        execute=_sqlite_tables,
    ))
