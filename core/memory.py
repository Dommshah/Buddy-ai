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
    ephemeral: bool = False  # privacy mode: keep in RAM, never write to disk
    passphrase: str | None = None  # when set, files are encrypted at rest
    _memories: dict[str, Any] = field(default_factory=dict, init=False)
    _conversations: list[dict[str, str]] = field(default_factory=list, init=False)
    _locked: bool = field(default=False, init=False)  # encrypted-but-unlockable → never overwrite

    def load(self) -> None:
        """Load memories from disk (transparently decrypting when sealed)."""
        from .crypto import is_encrypted, read_maybe_encrypted

        self.memory_dir.mkdir(parents=True, exist_ok=True)

        mem_file = self.memory_dir / "memories.json"
        if mem_file.exists():
            try:
                if is_encrypted(mem_file.read_bytes()) and not self.passphrase:
                    raise ValueError("encrypted without passphrase")
                self._memories = json.loads(
                    read_maybe_encrypted(mem_file, self.passphrase)
                )
            except ValueError:
                # Sealed data we can't unlock: FAIL-CLOSED. Do not continue to
                # write plaintext/keys over the sealed file in later save() calls.
                logging.warning("Memory locked (encrypted, no usable passphrase) — refusing to overwrite sealed data.")
                self._memories = {}
                self._locked = True
            except (json.JSONDecodeError, OSError):
                self._memories = {}

        conv_file = self.memory_dir / "conversations.json"
        if conv_file.exists():
            try:
                if is_encrypted(conv_file.read_bytes()) and not self.passphrase:
                    raise ValueError("encrypted without passphrase")
                self._conversations = json.loads(
                    read_maybe_encrypted(conv_file, self.passphrase)
                )
            except ValueError:
                logging.warning("Conversations locked (encrypted, no usable passphrase) — refusing to overwrite sealed data.")
                self._conversations = []
                self._locked = True
            except (json.JSONDecodeError, OSError):
                self._conversations = []

    def save(self) -> None:
        """Persist memories to disk (skipped in ephemeral/privacy mode)."""
        # Always cap in-memory size, even in ephemeral mode
        self._conversations = self._conversations[-self.max_items :]
        if self.ephemeral:
            logging.debug("Privacy mode: skipping memory persistence.")
            return
        if self._locked:
            logging.warning(
                "Cannot save: memory files are encrypted and no usable passphrase was provided. "
                "Run with DATA_PASSPHRASE (or set it) to unlock and resume persistence."
            )
            return
        from .crypto import write_sealed

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        write_sealed(
            self.memory_dir / "memories.json",
            json.dumps(self._memories, indent=2),
            self.passphrase,
        )

        write_sealed(
            self.memory_dir / "conversations.json",
            json.dumps(self._conversations, indent=2, ensure_ascii=False),
            self.passphrase,
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

        # Add categorized memories (bounded to avoid unbounded prompt growth).
        for key, data in list(self._memories.items())[-50:]:
            if not isinstance(data, dict):
                continue
            cat = str(data.get("category", "note"))
            value = str(data.get("value", ""))[:500]
            lines.append(f"[{cat}] {key}: {value}")

        # Add recent conversation summary
        recent = self._conversations[-10:]
        if recent:
            lines.append("\nRecent conversation history:")
            for conv in recent:
                if not isinstance(conv, dict):
                    continue
                lines.append(f"  User: {str(conv.get('user', ''))[:150]}")
                lines.append(f"  Agent: {str(conv.get('agent', ''))[:150]}")

        return "\n".join(lines) if lines else "(No prior context)"

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search memories by keyword."""
        query_lower = query.lower()
        results = []
        for key, data in self._memories.items():
            if query_lower in key.lower() or query_lower in str(data.get("value", "")).lower():
                results.append({"key": key, **data})
        return results
