"""Persistent memory manager for the AI agent."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    key: str
    value: str
    category: str
    created: str
    updated: str


@dataclass
class MemoryManager:
    """Manages persistent memory storage and conversation history."""

    memory_dir: Path = field(default_factory=lambda: Path("./data/memory"))
    max_items: int = 500
    _memories: dict[str, Any] = field(default_factory=dict, init=False)
    _conversations: list[dict[str, str]] = field(default_factory=list, init=False)

    def load(self) -> None:
        """Load memories from disk."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        mem_file = self.memory_dir / "memories.json"
        if mem_file.exists():
            try:
                self._memories = json.loads(mem_file.read_text())
            except (json.JSONDecodeError, OSError):
                self._memories = {}

        conv_file = self.memory_dir / "conversations.json"
        if conv_file.exists():
            try:
                self._conversations = json.loads(conv_file.read_text())
            except (json.JSONDecodeError, OSError):
                self._conversations = []

    def save(self) -> None:
        """Persist memories to disk."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_dir / "memories.json").write_text(json.dumps(self._memories, indent=2))

        # Keep only last N conversations
        self._conversations = self._conversations[-self.max_items :]
        (self.memory_dir / "conversations.json").write_text(
            json.dumps(self._conversations, indent=2, ensure_ascii=False)
        )

    def add_conversation(self, user_msg: str, agent_msg: str) -> None:
        """Record a conversation exchange."""
        self._conversations.append(
            {"user": user_msg, "agent": agent_msg, "timestamp": datetime.now().isoformat()}
        )
        self.save()

    def get_context_string(self) -> str:
        """Build a context string from recent memories for the system prompt."""
        lines: list[str] = []

        # Add categorized memories
        for key, data in self._memories.items():
            cat = data.get("category", "note")
            lines.append(f"[{cat}] {key}: {data.get('value', '')}")

        # Add recent conversation summary
        recent = self._conversations[-10:]
        if recent:
            lines.append("\nRecent conversation history:")
            for conv in recent:
                lines.append(f"  User: {conv['user'][:150]}")
                lines.append(f"  Agent: {conv['agent'][:150]}")

        return "\n".join(lines) if lines else "(No prior context)"

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search memories by keyword."""
        query_lower = query.lower()
        results = []
        for key, data in self._memories.items():
            if query_lower in key.lower() or query_lower in str(data.get("value", "")).lower():
                results.append({"key": key, **data})
        return results
