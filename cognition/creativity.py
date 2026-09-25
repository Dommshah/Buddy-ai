"""
Creativity & Ideation Module — brainstorming, creative writing,
idea generation, and innovation frameworks.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Idea:
    title: str
    description: str
    category: str
    feasibility: float  # 0-1
    impact: float  # 0-1
    novelty: float  # 0-1
    tags: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return (self.feasibility + self.impact + self.novelty) / 3


class CreativityEngine:
    """Generates creative ideas, content, and solutions."""

    def brainstorm(self, topic: str, num_ideas: int = 10, approach: str = "divergent") -> list[Idea]:
        """Generate brainstormed ideas for a topic."""
        ideas: list[Idea] = []

        if approach == "divergent":
            ideas = self._divergent_brainstorm(topic, num_ideas)
        elif approach == "convergent":
            ideas = self._convergent_brainstorm(topic, num_ideas)
        elif approach == "scamper":
            ideas = self._scamper_brainstorm(topic)
        elif approach == "random_association":
            ideas = self._random_association(topic, num_ideas)
        else:
            ideas = self._divergent_brainstorm(topic, num_ideas)

        ideas.sort(key=lambda i: i.score, reverse=True)
        return ideas[:num_ideas]

    def _divergent_brainstorm(self, topic: str, count: int) -> list[Idea]:
        """Generate diverse, non-obvious ideas."""
        angles = [
            "reverse", "extreme", "combine", "simplify", "digitize",
            "gamify", "localize", "globalize", "premium", "democratize",
            "automate", "personalize", "ecosystem", "subscription", "open_source",
        ]

        idea_templates = [
            "What if we {angle} {topic}?",
            "A {angle} approach to {topic}.",
            "Combine {topic} with {angle} methodology.",
            "Create a {angle} version of {topic}.",
        ]

        ideas: list[Idea] = []
        for i in range(min(count, len(angles))):
            angle = angles[i % len(angles)]
            template = idea_templates[i % len(idea_templates)]
            description = template.format(angle=angle, topic=topic)

            ideas.append(
                Idea(
                    title=f"{angle.title()} {topic.title()}",
                    description=description,
                    category="divergent",
                    feasibility=random.uniform(0.4, 0.9),
                    impact=random.uniform(0.5, 0.95),
                    novelty=random.uniform(0.5, 0.95),
                    tags=[angle, topic.lower()],
                )
            )

        return ideas

    def _convergent_brainstorm(self, topic: str, count: int) -> list[Idea]:
        """Generate focused, practical ideas."""
        frameworks = [
            "improve_existing", "reduce_cost", "increase_reach",
            "enhance用户体验", "add_mobile", "add_ai",
            "partner_integration", "subscription_model", "freemium",
            "community_driven",
        ]

        ideas: list[Idea] = []
        for i in range(min(count, len(frameworks))):
            fw = frameworks[i]
            ideas.append(
                Idea(
                    title=f"{fw.replace('_', ' ').title()} for {topic}",
                    description=f"Apply {fw.replace('_', ' ')} strategy to {topic}",
                    category="convergent",
                    feasibility=random.uniform(0.6, 0.95),
                    impact=random.uniform(0.4, 0.8),
                    novelty=random.uniform(0.3, 0.7),
                    tags=[fw, topic.lower()],
                )
            )

        return ideas

    def _scamper_brainstorm(self, topic: str) -> list[Idea]:
        """SCAMPER framework: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse."""
        scamper_ops = {
            "Substitute": "Replace a component of {topic} with something unexpected",
            "Combine": "Merge {topic} with an unrelated concept",
            "Adapt": "Adapt {topic} for a completely different use case",
            "Modify": "Exaggerate or minimize a key aspect of {topic}",
            "Put to other use": "Use {topic} in a context it was never designed for",
            "Eliminate": "Remove the most essential part of {topic}",
            "Reverse": "Do the exact opposite of how {topic} normally works",
        }

        ideas: list[Idea] = []
        for op, template in scamper_ops.items():
            ideas.append(
                Idea(
                    title=f"SCAMPER: {op} → {topic}",
                    description=template.format(topic=topic),
                    category="scamper",
                    feasibility=random.uniform(0.5, 0.85),
                    impact=random.uniform(0.5, 0.9),
                    novelty=random.uniform(0.6, 0.95),
                    tags=["scamper", op.lower(), topic.lower()],
                )
            )

        return ideas

    def _random_association(self, topic: str, count: int) -> list[Idea]:
        """Generate ideas through random concept association."""
        random_concepts = [
            "biomimicry", "blockchain", "space exploration", "gaming",
            "nature", "music", "architecture", "cooking", "sports",
            "meditation", "quantum computing", "ancient history", "street art",
            "marine biology", "fashion", "robotics", "poetry",
        ]

        random.shuffle(random_concepts)
        ideas: list[Idea] = []

        for i in range(min(count, len(random_concepts))):
            concept = random_concepts[i]
            ideas.append(
                Idea(
                    title=f"{topic} × {concept.title()}",
                    description=f"What happens when {topic} meets {concept}?",
                    category="association",
                    feasibility=random.uniform(0.3, 0.8),
                    impact=random.uniform(0.4, 0.9),
                    novelty=random.uniform(0.7, 0.99),
                    tags=[concept, topic.lower()],
                )
            )

        return ideas

    def creative_writing_prompt(self, genre: str = "any", mood: str = "any") -> str:
        """Generate a creative writing prompt."""
        settings = [
            "a crumbling library at the edge of reality",
            "a train station where trains arrive from different time periods",
            "a garden that grows memories instead of flowers",
            "a city where gravity works in every direction",
            "a workshop that builds emotions from raw materials",
            "an ocean where the water is made of liquid starlight",
        ]

        characters = [
            "a retired thief who can hear objects whisper their history",
            "a child who ages backwards but retains all memories",
            "an AI that has started dreaming",
            "a translator who can only speak the truth",
            "a chef whose food changes the eater's emotions",
            "a cartographer mapping places that only exist in dreams",
        ]

        conflicts = [
            "but everything they build disappears at sunrise",
            "and they discover the one thing they cannot create",
            "until they realize they are the last person who remembers colors",
            "but a mysterious stranger offers them a deal that defies logic",
            "and they must choose between two equally impossible futures",
        ]

        setting = random.choice(settings)
        character = random.choice(characters)
        conflict = random.choice(conflicts)

        return (
            f"In {setting}, {character} {conflict}. "
            f"Write a {genre} story in a {mood} mood. "
            f"Include an unexpected twist and end with more questions than answers."
        )

    def innovation_framework(self, problem: str) -> dict[str, Any]:
        """Apply structured innovation frameworks to a problem."""
        return {
            "problem": problem,
            "six_thinking_hats": {
                "white_facts": f"What do we know factually about {problem}?",
                "red_emotions": f"How do people feel about {problem}?",
                "black_critical": f"What are the risks and downsides of {problem}?",
                "yellow_optimistic": f"What are the benefits and opportunities in {problem}?",
                "green_creative": f"What new ideas can we generate for {problem}?",
                "blue_process": f"How should we approach solving {problem}?",
            },
            "five_whys": [
                f"Why does {problem} exist?",
                "Why does that cause exist?",
                "Why is that the case?",
                "Why hasn't it been solved before?",
                "Why is now the right time to solve it?",
            ],
            "how_might_we": [
                f"How might we eliminate {problem} entirely?",
                f"How might we make {problem} 10x easier?",
                f"How might we turn {problem} into an advantage?",
                f"How might we involve the community in solving {problem}?",
            ],
        }

    def idea_selection_matrix(self, ideas: list[Idea]) -> dict[str, Any]:
        """Score and rank ideas using a weighted matrix."""
        scored = []
        for idea in ideas:
            total_score = idea.score
            scored.append({
                "title": idea.title,
                "score": round(total_score, 3),
                "feasibility": round(idea.feasibility, 2),
                "impact": round(idea.impact, 2),
                "novelty": round(idea.novelty, 2),
                "recommendation": (
                    "Pursue immediately" if total_score > 0.8
                    else "Worth exploring" if total_score > 0.6
                    else "Needs more development" if total_score > 0.4
                    else "Deprioritize"
                ),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"ranked_ideas": scored, "top_pick": scored[0] if scored else None}
