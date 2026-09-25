"""
Knowledge Base — structured knowledge from open-source data patterns,
technical documentation, and accumulated learning.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeEntry:
    id: str
    topic: str
    category: str
    content: str
    source: str
    confidence: float
    tags: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""

    def __post_init__(self) -> None:
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.updated:
            self.updated = datetime.now().isoformat()


class KnowledgeBase:
    """
    Persistent knowledge base built from open-source patterns,
    technical documentation, and accumulated agent learning.
    """

    def __init__(self, data_dir: str = "./data/knowledge") -> None:
        self._data_dir = Path(data_dir)
        self._entries: dict[str, KnowledgeEntry] = {}
        self._categories: dict[str, list[str]] = {}
        self._load()
        self._init_foundational_knowledge()

    def _load(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        kb_file = self._data_dir / "knowledge_base.json"
        if kb_file.exists():
            try:
                data = json.loads(kb_file.read_text())
                for item in data:
                    entry = KnowledgeEntry(**item)
                    self._entries[entry.id] = entry
                    self._categories.setdefault(entry.category, []).append(entry.id)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "id": e.id, "topic": e.topic, "category": e.category,
                "content": e.content, "source": e.source, "confidence": e.confidence,
                "tags": e.tags, "related": e.related,
                "created": e.created, "updated": e.updated,
            }
            for e in self._entries.values()
        ]
        (self._data_dir / "knowledge_base.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _init_foundational_knowledge(self) -> None:
        """Initialize with foundational knowledge from open-source patterns."""
        if len(self._entries) > 10:
            return  # Already initialized

        foundational = [
            KnowledgeEntry(id="kb-python-best", topic="Python Best Practices", category="programming",
                content="Use virtual environments, type hints, docstrings. Follow PEP 8. Use pytest for testing. Prefer f-strings. Use pathlib over os.path.",
                source="open-source-patterns", confidence=0.95, tags=["python", "best-practices"]),
            KnowledgeEntry(id="kb-security-owasp", topic="OWASP Top 10", category="security",
                content="A01:Broken Access Control, A02:Cryptographic Failures, A03:Injection, A04:Insecure Design, A05:Security Misconfiguration, A06:Vulnerable Components, A07:Auth Failures, A08:Data Integrity, A09:Logging Failures, A10:SSRF",
                source="owasp.org", confidence=0.98, tags=["security", "web", "owasp"]),
            KnowledgeEntry(id="kb-git-workflow", topic="Git Workflow", category="tools",
                content="Use feature branches, squash commits, write clear commit messages. Use conventional commits: feat:, fix:, docs:, style:, refactor:, test:, chore:",
                source="open-source-patterns", confidence=0.95, tags=["git", "workflow"]),
            KnowledgeEntry(id="kb-docker", topic="Docker Best Practices", category="devops",
                content="Use multi-stage builds, minimize layers, use .dockerignore, don't run as root, use specific base image tags, scan images for vulnerabilities.",
                source="docs.docker.com", confidence=0.92, tags=["docker", "containers"]),
            KnowledgeEntry(id="kb-api-design", topic="REST API Design", category="architecture",
                content="Use nouns for resources, HTTP verbs for actions. Version APIs. Use proper status codes. Implement pagination. Use HATEOAS. Validate input. Rate limit.",
                source="open-source-patterns", confidence=0.93, tags=["api", "rest", "architecture"]),
            KnowledgeEntry(id="kb-llm-prompts", topic="Prompt Engineering", category="ai",
                content="Be specific and clear. Provide examples. Use system messages for role. Chain-of-thought for complex reasoning. Few-shot for consistency. Temperature for creativity control.",
                source="openai-docs", confidence=0.94, tags=["llm", "prompts", "ai"]),
            KnowledgeEntry(id="kb-data-structs", topic="Essential Data Structures", category="computer-science",
                content="Arrays: O(1) access. Linked Lists: O(1) insert. Hash Maps: O(1) lookup. Trees: O(log n) balanced. Graphs: BFS/DFS traversal. Heaps: O(log n) insert/extract.",
                source="open-source-patterns", confidence=0.97, tags=["algorithms", "data-structures"]),
            KnowledgeEntry(id="kb-microservices", topic="Microservices Patterns", category="architecture",
                content="API Gateway, Service Discovery, Circuit Breaker, Event Sourcing, CQRS, Saga Pattern, Sidecar Pattern, Strangler Fig Pattern.",
                source="open-source-patterns", confidence=0.91, tags=["microservices", "architecture"]),
            KnowledgeEntry(id="kb-async-python", topic="Async Python", category="programming",
                content="Use asyncio for I/O-bound tasks. Use aiohttp for async HTTP. Use async generators. Avoid blocking in async code. Use asyncio.gather for concurrency.",
                source="docs.python.org", confidence=0.93, tags=["python", "async", "concurrency"]),
            KnowledgeEntry(id="kb-testing", topic="Testing Strategies", category="quality",
                content="Test pyramid: Many unit tests, fewer integration tests, minimal E2E tests. Use mocks for external dependencies. Test edge cases. Use property-based testing for algorithms.",
                source="open-source-patterns", confidence=0.94, tags=["testing", "quality"]),
        ]

        for entry in foundational:
            if entry.id not in self._entries:
                self._entries[entry.id] = entry
                self._categories.setdefault(entry.category, []).append(entry.id)

        self._save()

    def add_entry(
        self,
        topic: str,
        category: str,
        content: str,
        source: str = "agent",
        confidence: float = 0.8,
        tags: list[str] | None = None,
    ) -> str:
        """Add a new knowledge entry."""
        entry_id = f"kb-{len(self._entries)}-{topic[:20].lower().replace(' ', '-')}"
        entry = KnowledgeEntry(
            id=entry_id,
            topic=topic,
            category=category,
            content=content,
            source=source,
            confidence=confidence,
            tags=tags or [],
        )
        self._entries[entry_id] = entry
        self._categories.setdefault(category, []).append(entry_id)
        self._save()
        return entry_id

    def query(self, query_text: str, category: str | None = None, limit: int = 10) -> list[KnowledgeEntry]:
        """Query knowledge base by text search."""
        query_words = set(query_text.lower().split())
        scored: list[tuple[float, KnowledgeEntry]] = []

        for entry in self._entries.values():
            if category and entry.category != category:
                continue
            entry_words = set(entry.topic.lower().split() + entry.content.lower().split() + entry.tags)
            overlap = len(query_words & entry_words)
            score = overlap * entry.confidence
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def get_by_category(self, category: str) -> list[KnowledgeEntry]:
        ids = self._categories.get(category, [])
        return [self._entries[i] for i in ids if i in self._entries]

    def get_categories(self) -> dict[str, int]:
        return {cat: len(ids) for cat, ids in self._categories.items()}

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "categories": self.get_categories(),
            "avg_confidence": sum(e.confidence for e in self._entries.values()) / max(len(self._entries), 1),
            "sources": list(set(e.source for e in self._entries.values())),
        }

    def get_context_for_llm(self) -> str:
        """Build context string for LLM from knowledge base."""
        lines = ["## Knowledge Base Context"]
        stats = self.get_stats()
        lines.append(f"Total entries: {stats['total_entries']}, Categories: {list(stats['categories'].keys())}")

        for category in list(stats["categories"].keys())[:5]:
            entries = self.get_by_category(category)[:3]
            if entries:
                lines.append(f"\n### {category.title()}")
                for entry in entries:
                    lines.append(f"- {entry.topic}: {entry.content[:150]}")

        return "\n".join(lines)
