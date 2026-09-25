"""
Autonomous Reasoning Loop — self-directed thinking, planning,
reflection, and adaptive decision-making.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ThoughtType(Enum):
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    HYPOTHESIS = "hypothesis"
    DECISION = "decision"
    REFLECTION = "reflection"
    ACTION = "action"
    SYNTHESIS = "synthesis"


@dataclass
class Thought:
    id: int
    type: ThoughtType
    content: str
    confidence: float
    timestamp: str = ""
    parent_id: int | None = None
    children: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AutonomousReasoner:
    """
    Self-directed reasoning engine that thinks, reflects,
    and makes decisions autonomously.
    """

    def __init__(self, max_thoughts: int = 50) -> None:
        self.max_thoughts = max_thoughts
        self._thoughts: list[Thought] = []
        self._current_chain: list[int] = []
        self._reflection_count = 0
        self._decision_log: list[dict[str, Any]] = []

    def think(self, input_text: str) -> dict[str, Any]:
        """Main autonomous thinking loop."""
        self._thoughts.clear()
        self._current_chain.clear()

        # Phase 1: Observe
        observation = self._observe(input_text)

        # Phase 2: Analyze
        analysis = self._analyze(observation)

        # Phase 3: Generate hypotheses
        hypotheses = self._hypothesize(analysis)

        # Phase 4: Evaluate & decide
        decision = self._decide(hypotheses)

        # Phase 5: Reflect
        reflection = self._reflect(decision)

        # Phase 6: Synthesize
        synthesis = self._synthesize()

        return {
            "input": input_text,
            "thought_chain": [t.content for t in self._thoughts],
            "total_thoughts": len(self._thoughts),
            "observation": observation.content,
            "analysis": analysis.content,
            "hypotheses": [h.content for h in hypotheses],
            "decision": decision.content,
            "reflection": reflection.content,
            "synthesis": synthesis.content,
            "confidence": synthesis.confidence,
            "thought_types": {tt.value: sum(1 for t in self._thoughts if t.type == tt) for tt in ThoughtType},
        }

    def _observe(self, input_text: str) -> Thought:
        """Observe and parse the input."""
        thought = Thought(
            id=len(self._thoughts),
            type=ThoughtType.OBSERVATION,
            content=f"Observing: {input_text[:500]}",
            confidence=0.95,
        )
        thought.metadata["original_input"] = input_text
        thought.metadata["word_count"] = len(input_text.split())
        self._thoughts.append(thought)
        self._current_chain.append(thought.id)
        return thought

    def _analyze(self, observation: Thought) -> Thought:
        """Analyze the observation for key elements."""
        input_text = observation.metadata.get("original_input", observation.content)
        words = input_text.lower().split()

        intent_signals = {
            "question": ["what", "how", "why", "when", "where", "who", "which", "can", "is", "are"],
            "command": ["do", "create", "write", "build", "fix", "run", "execute", "send", "make"],
            "research": ["research", "find", "search", "investigate", "explore", "learn", "discover"],
            "analysis": ["analyze", "compare", "evaluate", "assess", "review", "audit", "check"],
            "creative": ["brainstorm", "imagine", "design", "innovate", "ideate"],
        }

        detected_intents: dict[str, float] = {}
        for intent, signals in intent_signals.items():
            matches = sum(1 for w in words if w in signals)
            if matches > 0:
                detected_intents[intent] = matches / len(words)

        primary_intent = max(detected_intents, key=detected_intents.get) if detected_intents else "general"

        thought = Thought(
            id=len(self._thoughts),
            type=ThoughtType.ANALYSIS,
            content=f"Analysis: Primary intent is '{primary_intent}' with {len(input_text.split())} words. Detected intents: {list(detected_intents.keys())}",
            confidence=0.8,
            parent_id=observation.id,
        )
        thought.metadata["intents"] = detected_intents
        thought.metadata["primary_intent"] = primary_intent
        self._thoughts.append(thought)
        self._current_chain.append(thought.id)
        observation.children.append(thought.id)
        return thought

    def _hypothesize(self, analysis: Thought) -> list[Thought]:
        """Generate possible approaches based on analysis."""
        primary_intent = analysis.metadata.get("primary_intent", "general")

        approach_map = {
            "question": [
                "Provide direct factual answer",
                "Break down the question and answer systematically",
                "Research and provide comprehensive answer",
            ],
            "command": [
                "Execute the command directly using available tools",
                "Plan the execution steps before acting",
                "Verify prerequisites and then execute",
            ],
            "research": [
                "Search web for comprehensive information",
                "Analyze existing knowledge and synthesize",
                "Use multi-source research with fact-checking",
            ],
            "analysis": [
                "Perform systematic data analysis",
                "Compare and contrast different aspects",
                "Apply structured analytical framework",
            ],
            "creative": [
                "Brainstorm multiple creative approaches",
                "Use SCAMPER or lateral thinking",
                "Combine ideas from different domains",
            ],
            "general": [
                "Address the request directly",
                "Gather more context if needed",
                "Provide comprehensive response",
            ],
        }

        approaches = approach_map.get(primary_intent, approach_map["general"])
        hypotheses: list[Thought] = []

        for i, approach in enumerate(approaches):
            thought = Thought(
                id=len(self._thoughts),
                type=ThoughtType.HYPOTHESIS,
                content=f"Approach {i+1}: {approach}",
                confidence=0.7 - i * 0.1,
                parent_id=analysis.id,
            )
            self._thoughts.append(thought)
            hypotheses.append(thought)
            analysis.children.append(thought.id)

        return hypotheses

    def _decide(self, hypotheses: list[Thought]) -> Thought:
        """Select the best approach based on confidence."""
        best = max(hypotheses, key=lambda h: h.confidence)

        decision = Thought(
            id=len(self._thoughts),
            type=ThoughtType.DECISION,
            content=f"Decision: {best.content}",
            confidence=best.confidence,
            parent_id=best.parent_id,
        )
        decision.metadata["chosen_hypothesis"] = best.content
        decision.metadata["alternatives"] = [h.content for h in hypotheses if h.id != best.id]
        self._thoughts.append(decision)
        self._current_chain.append(decision.id)
        best.children.append(decision.id)

        self._decision_log.append({
            "decision": best.content,
            "alternatives": len(hypotheses),
            "confidence": best.confidence,
            "timestamp": datetime.now().isoformat(),
        })

        return decision

    def _reflect(self, decision: Thought) -> Thought:
        """Reflect on the decision quality."""
        self._reflection_count += 1

        strengths = []
        weaknesses = []

        if decision.confidence > 0.8:
            strengths.append("High confidence in approach")
        elif decision.confidence > 0.5:
            strengths.append("Moderate confidence")
        else:
            weaknesses.append("Low confidence — consider alternatives")

        if len(self._thoughts) > 3:
            strengths.append("Multi-step reasoning applied")
        else:
            weaknesses.append("Limited reasoning depth")

        content = (
            f"Reflection #{self._reflection_count}: "
            f"Strengths: {'; '.join(strengths)}. "
            f"Areas to watch: {'; '.join(weaknesses)}. "
            f"Overall assessment: The reasoning chain is {'solid' if len(strengths) > len(weaknesses) else 'needs improvement'}."
        )

        thought = Thought(
            id=len(self._thoughts),
            type=ThoughtType.REFLECTION,
            content=content,
            confidence=0.75,
            parent_id=decision.id,
        )
        thought.metadata["strengths"] = strengths
        thought.metadata["weaknesses"] = weaknesses
        self._thoughts.append(thought)
        self._current_chain.append(thought.id)
        decision.children.append(thought.id)
        return thought

    def _synthesize(self) -> Thought:
        """Synthesize all thoughts into a final conclusion."""
        thought_types = {tt: 0 for tt in ThoughtType}
        for t in self._thoughts:
            thought_types[t.type] += 1

        avg_confidence = (
            sum(t.confidence for t in self._thoughts) / len(self._thoughts)
            if self._thoughts else 0
        )

        content = (
            f"Synthesis: Processed {len(self._thoughts)} thoughts across {len(ThoughtType)} phases. "
            f"Reasoning chain depth: {len(self._current_chain)}. "
            f"Average confidence: {avg_confidence:.0%}. "
            f"Decision quality: {'High' if avg_confidence > 0.7 else 'Moderate' if avg_confidence > 0.5 else 'Low'}."
        )

        thought = Thought(
            id=len(self._thoughts),
            type=ThoughtType.SYNTHESIS,
            content=content,
            confidence=avg_confidence,
        )
        thought.metadata["total_thoughts"] = len(self._thoughts)
        thought.metadata["thought_distribution"] = {tt.value: c for tt, c in thought_types.items()}
        self._thoughts.append(thought)
        return thought

    def get_thought_chain(self) -> list[dict[str, Any]]:
        return [
            {
                "id": t.id,
                "type": t.type.value,
                "content": t.content,
                "confidence": t.confidence,
                "parent_id": t.parent_id,
            }
            for t in self._thoughts
        ]

    def get_reasoning_summary(self) -> str:
        lines = [f"=== Autonomous Reasoning Summary ===", f"Thoughts generated: {len(self._thoughts)}", ""]
        for t in self._thoughts:
            icon = {
                ThoughtType.OBSERVATION: "👁",
                ThoughtType.ANALYSIS: "🔍",
                ThoughtType.HYPOTHESIS: "💡",
                ThoughtType.DECISION: "⚖️",
                ThoughtType.REFLECTION: "🪞",
                ThoughtType.SYNTHESIS: "🎯",
            }.get(t.type, "•")
            lines.append(f"  {icon} [{t.type.value:12}] {t.content[:100]} (conf: {t.confidence:.0%})")
        return "\n".join(lines)
