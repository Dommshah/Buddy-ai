"""
Research Engine — orchestrates deep research, fact verification,
source analysis, and knowledge synthesis.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .browser import EnhancedBrowser, ResearchResult


@dataclass
class ResearchReport:
    query: str
    executive_summary: str
    detailed_findings: list[dict[str, str]]
    sources: list[dict[str, str]]
    key_insights: list[str]
    methodology: str
    confidence_score: float
    limitations: list[str]
    recommendations: list[str]
    generated_at: str = ""
    word_count: int = 0

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()


class ResearchEngine:
    """Comprehensive research engine for deep information gathering."""

    def __init__(self) -> None:
        self.browser = EnhancedBrowser()
        self._research_cache: dict[str, ResearchResult] = {}

    def quick_research(self, query: str) -> ResearchResult:
        """Quick single-depth research."""
        return self.browser.deep_research(query, depth=1, max_sources=5)

    def standard_research(self, query: str) -> ResearchResult:
        """Standard depth research."""
        return self.browser.deep_research(query, depth=2, max_sources=8)

    def deep_research(self, query: str) -> ResearchResult:
        """Deep multi-level research."""
        return self.browser.deep_research(query, depth=3, max_sources=12)

    def exhaustive_research(self, query: str) -> ResearchResult:
        """Exhaustive research with maximum depth."""
        return self.browser.deep_research(query, depth=5, max_sources=20)

    def generate_report(self, query: str, depth: int = 3) -> ResearchReport:
        """Generate a comprehensive research report."""
        result = self.browser.deep_research(query, depth=depth)

        # Structure findings
        findings: list[dict[str, str]] = []
        for i, source in enumerate(result.sources[:8], 1):
            findings.append({
                "source": source.title or f"Source {i}",
                "url": source.url,
                "key_point": source.content[:300] if source.content else "No content extracted",
                "word_count": str(source.word_count),
            })

        # Generate insights
        insights = self._generate_insights(result)

        # Generate recommendations
        recommendations = self._generate_recommendations(query, result)

        report = ResearchReport(
            query=query,
            executive_summary=result.summary,
            detailed_findings=findings,
            sources=result.citations,
            key_insights=insights,
            methodology=f"Multi-source web research with depth={depth}, analyzing {len(result.sources)} sources ({result.total_words:,} total words)",
            confidence_score=result.confidence,
            limitations=[
                "Based on web sources, may not include paywalled content",
                "Automated extraction may miss nuanced information",
                "Research depth limited by source availability",
            ],
            recommendations=recommendations,
            word_count=result.total_words,
        )

        return report

    def fact_check(self, claim: str) -> dict[str, Any]:
        """Verify a claim against web sources."""
        result = self.browser.deep_research(claim, depth=2, max_sources=5)

        supporting = 0
        contradicting = 0
        neutral = 0

        for source in result.sources:
            text_lower = source.content.lower()
            claim_words = set(claim.lower().split())
            source_words = set(text_lower.split())
            overlap = len(claim_words & source_words)

            if overlap > len(claim_words) * 0.3:
                if any(w in text_lower for w in ["confirmed", "true", "correct", "agree"]):
                    supporting += 1
                elif any(w in text_lower for w in ["false", "incorrect", "myth", "debunked", "not true"]):
                    contradicting += 1
                else:
                    neutral += 1

        total = supporting + contradicting + neutral
        confidence = (supporting / total) if total > 0 else 0.5

        return {
            "claim": claim,
            "verdict": "Supported" if supporting > contradicting else "Contradicted" if contradicting > supporting else "Inconclusive",
            "confidence": round(confidence, 2),
            "supporting_sources": supporting,
            "contradicting_sources": contradicting,
            "neutral_sources": neutral,
            "total_sources": total,
            "sources_checked": [s.url for s in result.sources],
        }

    def compare_topics(self, topic_a: str, topic_b: str) -> dict[str, Any]:
        """Research and compare two topics."""
        result_a = self.browser.deep_research(topic_a, depth=2, max_sources=5)
        result_b = self.browser.deep_research(topic_b, depth=2, max_sources=5)

        comparison = {
            "topic_a": topic_a,
            "topic_b": topic_b,
            "topic_a_sources": len(result_a.sources),
            "topic_b_sources": len(result_b.sources),
            "topic_a_words": result_a.total_words,
            "topic_b_words": result_b.total_words,
            "topic_a_summary": result_a.summary[:500],
            "topic_b_summary": result_b.summary[:500],
        }

        common = set(result_a.key_findings) & set(result_b.key_findings)
        comparison["common_findings"] = list(common)[:5]
        comparison["unique_to_a"] = [f for f in result_a.key_findings if f not in common][:5]
        comparison["unique_to_b"] = [f for f in result_b.key_findings if f not in common][:5]

        return comparison

    def get_trending_topics(self, domain: str = "technology") -> list[dict[str, str]]:
        """Find trending topics in a domain."""
        trending = self.browser.search_and_collect(f"trending {domain} topics 2024 2025", max_results=5)
        topics: list[dict[str, str]] = []
        for page in trending:
            topics.append({
                "title": page.title,
                "url": page.url,
                "snippet": page.content[:200] if page.content else "",
            })
        return topics

    def _generate_insights(self, result: ResearchResult) -> list[str]:
        insights: list[str] = []
        if result.sources:
            avg_words = result.total_words // len(result.sources)
            insights.append(f"Analyzed {len(result.sources)} sources with average {avg_words} words each")

        if result.key_findings:
            insights.append(f"Found {len(result.key_findings)} key findings across sources")

        if result.confidence > 0.7:
            insights.append(f"High confidence ({result.confidence:.0%}) based on source diversity")
        elif result.confidence > 0.4:
            insights.append(f"Moderate confidence ({result.confidence:.0%}) — additional sources recommended")
        else:
            insights.append(f"Low confidence ({result.confidence:.0%}) — limited source availability")

        return insights

    def _generate_recommendations(self, query: str, result: ResearchResult) -> list[str]:
        recs: list[str] = []
        if len(result.sources) < 3:
            recs.append("Consider expanding search to additional sources")
        if result.total_words < 1000:
            recs.append("Results are limited — try more specific queries")
        recs.append(f"For deeper analysis, run with increased depth parameter")
        recs.append(f"Cross-reference findings with domain-specific databases")
        return recs
