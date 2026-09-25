"""
Learning System — learns from interactions, stores patterns,
improves responses over time, and builds a knowledge base.
"""
from __future__ import annotations

import json
import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LearningEntry:
    id: str
    category: str
    input_pattern: str
    learned_output: str
    confidence: float
    times_used: int = 0
    times_correct: int = 0
    created: str = ""
    last_used: str = ""

    def __post_init__(self) -> None:
        if not self.created:
            self.created = datetime.now().isoformat()


@dataclass
class KnowledgeFact:
    topic: str
    fact: str
    source: str
    confidence: float
    related_topics: list[str] = field(default_factory=list)
    created: str = ""

    def __post_init__(self) -> None:
        if not self.created:
            self.created = datetime.now().isoformat()


@dataclass
class LearningSystem:
    """
    Adaptive learning system that stores learned patterns,
    knowledge facts, and improves over time.
    """

    data_dir: Path = field(default_factory=lambda: Path("./data/learning"))
    _patterns: dict[str, LearningEntry] = field(default_factory=dict, init=False)
    _knowledge: list[KnowledgeFact] = field(default_factory=list, init=False)
    _interaction_log: list[dict[str, Any]] = field(default_factory=list, init=False)
    _skill_scores: dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._load()

    def _load(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

        patterns_file = self.data_dir / "patterns.json"
        if patterns_file.exists():
            try:
                data = json.loads(patterns_file.read_text())
                self._patterns = {k: LearningEntry(**v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError):
                self._patterns = {}

        knowledge_file = self.data_dir / "knowledge.json"
        if knowledge_file.exists():
            try:
                data = json.loads(knowledge_file.read_text())
                self._knowledge = [KnowledgeFact(**f) for f in data]
            except (json.JSONDecodeError, KeyError):
                self._knowledge = []

        interactions_file = self.data_dir / "interactions.json"
        if interactions_file.exists():
            try:
                self._interaction_log = json.loads(interactions_file.read_text())
            except json.JSONDecodeError:
                self._interaction_log = []

        skills_file = self.data_dir / "skills.json"
        if skills_file.exists():
            try:
                self._skill_scores = json.loads(skills_file.read_text())
            except json.JSONDecodeError:
                self._skill_scores = {}

    def _save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

        (self.data_dir / "patterns.json").write_text(
            json.dumps(
                {k: v.__dict__ for k, v in self._patterns.items()},
                indent=2, ensure_ascii=False,
            )
        )
        (self.data_dir / "knowledge.json").write_text(
            json.dumps([f.__dict__ for f in self._knowledge], indent=2, ensure_ascii=False)
        )
        self._interaction_log = self._interaction_log[-1000:]
        (self.data_dir / "interactions.json").write_text(
            json.dumps(self._interaction_log, indent=2, ensure_ascii=False)
        )
        (self.data_dir / "skills.json").write_text(
            json.dumps(self._skill_scores, indent=2)
        )

    def learn_from_interaction(
        self, user_input: str, agent_response: str, feedback: str | None = None
    ) -> None:
        """Record an interaction for future learning."""
        entry = {
            "input": user_input,
            "output": agent_response,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
        }
        self._interaction_log.append(entry)

        if feedback:
            self._update_skill_score(user_input, feedback)

        self._save()

    def _update_skill_score(self, task_description: str, feedback: str) -> None:
        """Update skill proficiency based on feedback."""
        skill = self._detect_skill_category(task_description)
        current = self._skill_scores.get(skill, 50.0)

        if "good" in feedback.lower() or "correct" in feedback.lower():
            self._skill_scores[skill] = min(100, current + 5)
        elif "wrong" in feedback.lower() or "bad" in feedback.lower():
            self._skill_scores[skill] = max(0, current - 3)

    def _detect_skill_category(self, text: str) -> str:
        """Detect which skill category a task belongs to."""
        text_lower = text.lower()
        categories = {
            "coding": ["code", "program", "function", "script", "debug", "bug", "compile"],
            "writing": ["write", "article", "essay", "blog", "content", "copy"],
            "analysis": ["analyze", "data", "statistics", "chart", "graph", "metric"],
            "research": ["research", "find", "search", "investigate", "explore"],
            "planning": ["plan", "strategy", "roadmap", "schedule", "organize"],
            "creative": ["creative", "brainstorm", "idea", "design", "imagine"],
            "security": ["security", "vulnerability", "audit", "encrypt", "auth"],
        }
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        return "general"

    def store_pattern(
        self, category: str, input_pattern: str, output: str, confidence: float = 0.7
    ) -> str:
        """Store a learned pattern."""
        pattern_id = hashlib.md5(f"{category}:{input_pattern}".encode()).hexdigest()[:12]

        if pattern_id in self._patterns:
            existing = self._patterns[pattern_id]
            existing.times_used += 1
            existing.confidence = (existing.confidence + confidence) / 2
            existing.learned_output = output
            existing.last_used = datetime.now().isoformat()
        else:
            self._patterns[pattern_id] = LearningEntry(
                id=pattern_id,
                category=category,
                input_pattern=input_pattern,
                learned_output=output,
                confidence=confidence,
                times_used=1,
                last_used=datetime.now().isoformat(),
            )

        self._save()
        return pattern_id

    def find_similar_patterns(self, query: str, limit: int = 5) -> list[LearningEntry]:
        """Find patterns similar to the query."""
        query_words = set(query.lower().split())
        scored = []

        for pattern in self._patterns.values():
            pattern_words = set(pattern.input_pattern.lower().split())
            overlap = len(query_words & pattern_words)
            total = max(len(query_words | pattern_words), 1)
            relevance = (overlap / total) * pattern.confidence
            scored.append((relevance, pattern))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def add_knowledge(
        self,
        topic: str,
        fact: str,
        source: str = "interaction",
        confidence: float = 0.8,
        related_topics: list[str] | None = None,
    ) -> None:
        """Store a knowledge fact."""
        self._knowledge.append(
            KnowledgeFact(
                topic=topic,
                fact=fact,
                source=source,
                confidence=confidence,
                related_topics=related_topics or [],
            )
        )
        self._save()

    def query_knowledge(self, topic: str) -> list[KnowledgeFact]:
        """Query knowledge base by topic."""
        topic_lower = topic.lower()
        results = []
        for fact in self._knowledge:
            if (
                topic_lower in fact.topic.lower()
                or topic_lower in fact.fact.lower()
                or any(topic_lower in rt.lower() for rt in fact.related_topics)
            ):
                results.append(fact)
        return sorted(results, key=lambda f: f.confidence, reverse=True)

    def get_learning_stats(self) -> dict[str, Any]:

        skill_summary = {}
        for skill, score in self._skill_scores.items():
            level = "Expert" if score >= 90 else "Advanced" if score >= 70 else "Intermediate" if score >= 50 else "Beginner"
            skill_summary[skill] = {"score": round(score, 1), "level": level}

        category_counts = Counter()
        for entry in self._interaction_log:
            cat = self._detect_skill_category(entry.get("input", ""))
            category_counts[cat] += 1

        return {
            "total_interactions": len(self._interaction_log),
            "patterns_stored": len(self._patterns),
            "knowledge_facts": len(self._knowledge),
            "skill_levels": skill_summary,
            "task_distribution": dict(category_counts.most_common(10)),
            "most_common_tasks": category_counts.most_common(5),
        }

    def get_context_for_llm(self) -> str:
        """Build a context string for the LLM from learned patterns."""
        lines: list[str] = []

        stats = self.get_learning_stats()
        if stats.get("total_interactions", 0) > 0:
            lines.append("## Learning Context")
            lines.append(f"Total interactions: {stats['total_interactions']}")
            lines.append(f"Patterns learned: {stats.get('patterns_stored', 0)}")
            lines.append(f"Knowledge facts: {stats.get('knowledge_facts', 0)}")

            if stats.get("skill_levels"):
                lines.append("\nProficiency levels:")
                for skill, data in stats["skill_levels"].items():
                    lines.append(f"  {skill}: {data['level']} ({data['score']}%)")

        recent_patterns = sorted(
            self._patterns.values(),
            key=lambda p: p.last_used or p.created,
            reverse=True,
        )[:5]
        if recent_patterns:
            lines.append("\nRecently used patterns:")
            for p in recent_patterns:
                lines.append(f"  [{p.category}] {p.input_pattern[:60]}")

        return "\n".join(lines) if lines else ""

    def get_adaptive_prompt_addition(self) -> str:
        """Generate dynamic prompt additions based on learned patterns."""
        lines: list[str] = []

        stats = self.get_learning_stats()
        task_dist = stats.get("task_distribution", {})

        if task_dist:
            primary_task = max(task_dist, key=task_dist.get)
            if task_dist[primary_task] > 5:
                lines.append(
                    f"The user frequently asks about {primary_task} tasks. "
                    f"Prioritize {primary_task}-related capabilities."
                )

        low_skills = [
            skill
            for skill, score in self._skill_scores.items()
            if score < 50
        ]
        if low_skills:
            lines.append(
                f"Areas needing improvement: {', '.join(low_skills)}. "
                f"Take extra care with these task types."
            )

        return "\n".join(lines)
