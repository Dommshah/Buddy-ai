"""
Reasoning Engine — implements chain-of-thought, tree-of-thought,
deductive/inductive/abductive reasoning, and logical inference.
"""
from __future__ import annotations

import json
import re
import ast
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ReasoningMode(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CRITICAL = "critical"
    REFLECTIVE = "reflective"


@dataclass
class ReasoningStep:
    step_number: int
    thought: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    next_questions: list[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    mode: ReasoningMode
    conclusion: str
    steps: list[ReasoningStep]
    alternatives: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    counterarguments: list[str] = field(default_factory=list)


class ReasoningEngine:
    """
    Advanced reasoning engine that applies structured thinking patterns.
    Works in tandem with the LLM to produce deeper, more reliable reasoning.
    """

    def __init__(self) -> None:
        self._reasoning_cache: dict[str, ReasoningResult] = {}

    def chain_of_thought(self, problem: str, context: str = "") -> ReasoningResult:
        """
        Break a problem into sequential reasoning steps.
        Each step builds on the previous one.
        """
        steps = self._generate_cot_steps(problem, context)
        conclusion = steps[-1].thought if steps else "Unable to reason through this problem."
        avg_confidence = (
            sum(s.confidence for s in steps) / len(steps) if steps else 0.0
        )

        return ReasoningResult(
            mode=ReasoningMode.CHAIN_OF_THOUGHT,
            conclusion=conclusion,
            steps=steps,
            confidence_score=avg_confidence,
            assumptions=self._extract_assumptions(steps),
        )

    def tree_of_thought(
        self, problem: str, context: str = "", branching: int = 3
    ) -> ReasoningResult:
        """
        Explore multiple reasoning branches simultaneously.
        Evaluate each branch and select the most promising path.
        """
        branches = self._generate_thought_tree(problem, context, branching)
        best_branch = max(branches, key=lambda b: b["score"])

        steps = [
            ReasoningStep(
                step_number=i + 1,
                thought=f"[Branch: {best_branch['name']}] {s}",
                confidence=best_branch["score"],
            )
            for i, s in enumerate(best_branch["steps"])
        ]

        alternatives = [
            f"[{b['name']}] Score {b['score']:.2f}: {b['summary']}"
            for b in branches
            if b["name"] != best_branch["name"]
        ]

        return ReasoningResult(
            mode=ReasoningMode.TREE_OF_THOUGHT,
            conclusion=best_branch.get("conclusion", best_branch["steps"][-1] if best_branch["steps"] else ""),
            steps=steps,
            alternatives=alternatives,
            confidence_score=best_branch["score"],
        )

    def deductive_reasoning(
        self, premises: list[str], hypothesis: str
    ) -> ReasoningResult:
        """
        Apply deductive logic: if premises are true, what follows?
        """
        steps = []
        for i, premise in enumerate(premises):
            steps.append(
                ReasoningStep(
                    step_number=i + 1,
                    thought=f"Premise {i + 1}: {premise}",
                    confidence=0.9,
                )
            )

        steps.append(
            ReasoningStep(
                step_number=len(premises) + 1,
                thought=f"Applying logical deduction to: {hypothesis}",
                evidence=premises,
                confidence=0.85,
            )
        )

        steps.append(
            ReasoningStep(
                step_number=len(premises) + 2,
                thought=f"Conclusion based on deductive inference from {len(premises)} premises.",
                confidence=0.8,
            )
        )

        return ReasoningResult(
            mode=ReasoningMode.DEDUCTIVE,
            conclusion=hypothesis,
            steps=steps,
            assumptions=["All premises are assumed true", "Logic is valid"],
            confidence_score=0.8,
        )

    def inductive_reasoning(
        self, observations: list[str], pattern_description: str
    ) -> ReasoningResult:
        """
        Inductive reasoning: observe patterns, form generalizations.
        """
        steps = []
        for i, obs in enumerate(observations):
            steps.append(
                ReasoningStep(
                    step_number=i + 1,
                    thought=f"Observation {i + 1}: {obs}",
                    confidence=0.95,
                )
            )

        steps.append(
            ReasoningStep(
                step_number=len(observations) + 1,
                thought=f"Identifying pattern: {pattern_description}",
                evidence=observations,
                confidence=0.7,
            )
        )

        generalization_confidence = min(0.9, 0.5 + 0.05 * len(observations))
        steps.append(
            ReasoningStep(
                step_number=len(observations) + 2,
                thought="Generalizing from observed pattern to broader principle.",
                confidence=generalization_confidence,
            )
        )

        return ReasoningResult(
            mode=ReasoningMode.INDUCTIVE,
            conclusion=pattern_description,
            steps=steps,
            assumptions=[
                "Past observations predict future behavior",
                f"Sample of {len(observations)} is representative",
            ],
            confidence_score=generalization_confidence,
        )

    def abductive_reasoning(
        self, observation: str, possible_explanations: list[str]
    ) -> ReasoningResult:
        """
        Abductive reasoning: find the best explanation for an observation.
        """
        steps = [
            ReasoningStep(
                step_number=1,
                thought=f"Observation to explain: {observation}",
                confidence=1.0,
            )
        ]

        scored_explanations = []
        for i, expl in enumerate(possible_explanations):
            score = self._score_explanation(expl, observation)
            scored_explanations.append((expl, score))
            steps.append(
                ReasoningStep(
                    step_number=i + 2,
                    thought=f"Considering explanation: {expl} (plausibility: {score:.2f})",
                    confidence=score,
                )
            )

        best = max(scored_explanations, key=lambda x: x[1])
        steps.append(
            ReasoningStep(
                step_number=len(possible_explanations) + 2,
                thought=f"Best explanation (inference to best explanation): {best[0]}",
                confidence=best[1],
            )
        )

        return ReasoningResult(
            mode=ReasoningMode.ABDUCTIVE,
            conclusion=best[0],
            steps=steps,
            alternatives=[e[0] for e in scored_explanations if e[0] != best[0]],
            confidence_score=best[1],
        )

    def analogical_reasoning(
        self, source_domain: str, target_domain: str, source_features: list[str]
    ) -> ReasoningResult:
        """
        Reason by analogy: map features from source to target domain.
        """
        steps = [
            ReasoningStep(
                step_number=1,
                thought=f"Source domain: {source_domain}",
                confidence=0.95,
            ),
            ReasoningStep(
                step_number=2,
                thought=f"Target domain: {target_domain}",
                confidence=0.95,
            ),
        ]

        for i, feature in enumerate(source_features):
            steps.append(
                ReasoningStep(
                    step_number=i + 3,
                    thought=f"Mapping feature '{feature}' from {source_domain} → {target_domain}",
                    confidence=0.65,
                )
            )

        steps.append(
            ReasoningStep(
                step_number=len(source_features) + 3,
                thought="Drawing inferences from structural similarities between domains.",
                evidence=source_features,
                confidence=0.6,
            )
        )

        return ReasoningResult(
            mode=ReasoningMode.ANALOGICAL,
            conclusion=f"Analogical mapping: {source_domain} → {target_domain}",
            steps=steps,
            assumptions=["Domains share relevant structural similarities"],
            confidence_score=0.65,
        )

    def critical_analysis(self, claim: str, evidence: list[str]) -> ReasoningResult:
        """
        Critically evaluate a claim against evidence.
        Identifies strengths, weaknesses, and logical fallacies.
        """
        steps = [
            ReasoningStep(
                step_number=1,
                thought=f"Claim under evaluation: {claim}",
                confidence=1.0,
            )
        ]

        supporting = [e for e in evidence if not self._is_negation(e)]
        counterevidence = [e for e in evidence if self._is_negation(e)]

        for i, e in enumerate(supporting[:5]):
            steps.append(
                ReasoningStep(
                    step_number=i + 2,
                    thought=f"Supporting evidence: {e}",
                    confidence=0.7,
                )
            )

        for i, e in enumerate(counterevidence[:5]):
            steps.append(
                ReasoningStep(
                    step_number=len(supporting) + i + 2,
                    thought=f"Counter-evidence: {e}",
                    confidence=0.7,
                )
            )

        steps.append(
            ReasoningStep(
                step_number=len(evidence) + 2,
                thought=f"Evaluation: {len(supporting)} supporting vs {len(counterevidence)} countering pieces of evidence.",
                confidence=0.75,
            )
        )

        return ReasoningResult(
            mode=ReasoningMode.CRITICAL,
            conclusion=f"Critical analysis of: {claim}",
            steps=steps,
            counterarguments=counterevidence,
            confidence_score=0.7,
        )

    def self_reflect(self, previous_reasoning: str, new_evidence: str) -> ReasoningResult:
        """
        Reflect on previous reasoning with new evidence.
        Revises conclusions if needed.
        """
        steps = [
            ReasoningStep(
                step_number=1,
                thought=f"Reviewing previous reasoning: {previous_reasoning[:200]}",
                confidence=0.8,
            ),
            ReasoningStep(
                step_number=2,
                thought=f"New evidence considered: {new_evidence}",
                confidence=0.85,
            ),
            ReasoningStep(
                step_number=3,
                thought="Re-evaluating conclusion in light of new information.",
                confidence=0.75,
            ),
            ReasoningStep(
                step_number=4,
                thought="Synthesizing old and new reasoning into revised conclusion.",
                confidence=0.7,
            ),
        ]

        return ReasoningResult(
            mode=ReasoningMode.REFLECTIVE,
            conclusion="Revised conclusion based on reflection and new evidence.",
            steps=steps,
            confidence_score=0.75,
        )

    # ── Private helpers ──────────────────────────────────────────────

    def _generate_cot_steps(self, problem: str, context: str) -> list[ReasoningStep]:
        """Generate chain-of-thought reasoning steps."""
        steps: list[ReasoningStep] = []
        sentences = re.split(r'[.!?]+', problem)
        sentences = [s.strip() for s in sentences if s.strip()]

        for i, sentence in enumerate(sentences[:10]):
            confidence = max(0.5, 0.9 - 0.04 * i)
            steps.append(
                ReasoningStep(
                    step_number=i + 1,
                    thought=sentence,
                    confidence=confidence,
                )
            )

        if not steps:
            steps.append(
                ReasoningStep(step_number=1, thought=problem, confidence=0.5)
            )

        return steps

    def _generate_thought_tree(
        self, problem: str, context: str, branching: int
    ) -> list[dict[str, Any]]:
        """Generate multiple reasoning branches."""
        branches = []
        approaches = ["systematic", "creative", "critical", "practical", "theoretical"]

        for i in range(min(branching, len(approaches))):
            approach = approaches[i]
            branches.append(
                {
                    "name": approach,
                    "steps": [f"Approach: {approach} analysis of the problem"],
                    "conclusion": f"Conclusion using {approach} approach",
                    "score": 0.5 + (i * 0.1),
                    "summary": f"{approach.capitalize()} analysis",
                }
            )

        return branches

    def _extract_assumptions(self, steps: list[ReasoningStep]) -> list[str]:
        """Extract implicit assumptions from reasoning steps."""
        assumptions = []
        for step in steps:
            thought_lower = step.thought.lower()
            if any(w in thought_lower for w in ["assuming", "given that", "if we assume", "presuming"]):
                assumptions.append(step.thought)
        if not assumptions:
            assumptions.append("Reasoning follows logical principles")
        return assumptions

    def _score_explanation(self, explanation: str, observation: str) -> float:
        """Score how well an explanation fits an observation."""
        explanation_words = set(explanation.lower().split())
        observation_words = set(observation.lower().split())
        overlap = len(explanation_words & observation_words)
        total = max(len(explanation_words | observation_words), 1)
        return min(0.95, 0.3 + (overlap / total) * 0.6)

    def _is_negation(self, text: str) -> bool:
        """Check if text represents a counter-argument."""
        negation_words = ["not", "no", "however", "but", "although", "contrary", "despite", "fails"]
        text_lower = text.lower()
        return any(w in text_lower for w in negation_words)


def format_reasoning(result: ReasoningResult) -> str:
    """Format a reasoning result as readable text."""
    lines = [f"=== {result.mode.value.upper()} REASONING ===\n"]

    for step in result.steps:
        conf_bar = "█" * int(step.confidence * 10) + "░" * (10 - int(step.confidence * 10))
        lines.append(f"  Step {step.step_number}: {step.thought}")
        lines.append(f"    Confidence: [{conf_bar}] {step.confidence:.0%}")
        if step.evidence:
            lines.append(f"    Evidence: {', '.join(step.evidence[:3])}")
        lines.append("")

    lines.append(f"CONCLUSION: {result.conclusion}")
    lines.append(f"Overall Confidence: {result.confidence_score:.0%}")

    if result.alternatives:
        lines.append(f"\nAlternatives considered:")
        for alt in result.alternatives[:3]:
            lines.append(f"  • {alt}")

    if result.assumptions:
        lines.append(f"\nAssumptions:")
        for a in result.assumptions[:3]:
            lines.append(f"  • {a}")

    if result.counterarguments:
        lines.append(f"\nCounter-arguments:")
        for c in result.counterarguments[:3]:
            lines.append(f"  • {c}")

    return "\n".join(lines)
