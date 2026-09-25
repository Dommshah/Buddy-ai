"""
Pattern Recognition & Prediction Engine — detects patterns in data,
identifies trends, and makes predictions.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Pattern:
    pattern_type: str
    description: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    locations: list[int] = field(default_factory=list)


@dataclass
class Prediction:
    target: str
    predicted_value: str
    confidence: float
    method: str
    supporting_patterns: list[str] = field(default_factory=list)


class PatternRecognizer:
    """Detects patterns in text, data, and behavior."""

    def detect_text_patterns(self, text: str) -> list[Pattern]:
        """Detect linguistic and structural patterns in text."""
        patterns: list[Pattern] = []
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) > 3:
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_len > 20:
                patterns.append(
                    Pattern(
                        pattern_type="complex_syntax",
                        description=f"Text uses complex sentence structure (avg {avg_len:.1f} words/sentence)",
                        confidence=0.8,
                    )
                )
            elif avg_len < 8:
                patterns.append(
                    Pattern(
                        pattern_type="simple_syntax",
                        description=f"Text uses simple sentence structure (avg {avg_len:.1f} words/sentence)",
                        confidence=0.8,
                    )
                )

        words = text.lower().split()
        word_freq = Counter(words)
        total = len(words)
        if total > 10:
            top_words = word_freq.most_common(5)
            patterns.append(
                Pattern(
                    pattern_type="key_topics",
                    description=f"Key topics: {', '.join(f'{w}({c}/{total})' for w, c in top_words)}",
                    confidence=0.9,
                )
            )

        sentiment_words = {
            "positive": ["good", "great", "excellent", "amazing", "wonderful", "love", "best", "happy", "beautiful"],
            "negative": ["bad", "terrible", "awful", "hate", "worst", "poor", "ugly", "sad", "horrible"],
        }
        for sentiment, s_words in sentiment_words.items():
            count = sum(1 for w in words if w in s_words)
            if count > 0:
                patterns.append(
                    Pattern(
                        pattern_type=f"sentiment_{sentiment}",
                        description=f"Detected {sentiment} sentiment ({count} indicators)",
                        confidence=min(0.9, 0.3 + count * 0.1),
                    )
                )

        repeated_phrases = self._find_repeated_phrases(text)
        if repeated_phrases:
            patterns.append(
                Pattern(
                    pattern_type="repetition",
                    description=f"Repeated phrases: {', '.join(repeated_phrases[:3])}",
                    confidence=0.85,
                    evidence=repeated_phrases,
                )
            )

        return patterns

    def detect_data_patterns(self, values: list[float]) -> list[Pattern]:
        """Detect patterns in numerical data."""
        if len(values) < 3:
            return []

        patterns: list[Pattern] = []

        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        if all(d > 0 for d in diffs):
            patterns.append(
                Pattern(
                    pattern_type="monotonic_increase",
                    description="Data shows consistent upward trend",
                    confidence=0.95,
                )
            )
        elif all(d < 0 for d in diffs):
            patterns.append(
                Pattern(
                    pattern_type="monotonic_decrease",
                    description="Data shows consistent downward trend",
                    confidence=0.95,
                )
            )

        if len(values) > 4:
            mean = sum(values) / len(values)
            std = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
            outliers = [i for i, v in enumerate(values) if abs(v - mean) > 2 * std]
            if outliers:
                patterns.append(
                    Pattern(
                        pattern_type="outliers",
                        description=f"Outliers detected at positions {outliers}",
                        confidence=0.8,
                        locations=outliers,
                    )
                )

        if len(values) > 6:
            window = len(values) // 3
            first_avg = sum(values[:window]) / window
            last_avg = sum(values[-window:]) / window
            change_pct = ((last_avg - first_avg) / max(abs(first_avg), 0.001)) * 100
            direction = "increasing" if change_pct > 0 else "decreasing"
            patterns.append(
                Pattern(
                    pattern_type="trend",
                    description=f"Overall trend: {direction} ({abs(change_pct):.1f}% change)",
                    confidence=min(0.9, 0.5 + len(values) * 0.02),
                )
            )

        if len(values) >= 4:
            autocorr = self._autocorrelation(values, 1)
            if abs(autocorr) > 0.6:
                patterns.append(
                    Pattern(
                        pattern_type="auto_correlation",
                        description=f"Strong temporal autocorrelation (r={autocorr:.2f})",
                        confidence=min(0.85, abs(autocorr)),
                    )
                )

        return patterns

    def detect_behavior_patterns(
        self, interactions: list[dict[str, Any]]
    ) -> list[Pattern]:
        """Detect patterns in user interaction history."""
        if len(interactions) < 5:
            return []

        patterns: list[Pattern] = []

        time_patterns = self._detect_temporal_patterns(interactions)
        patterns.extend(time_patterns)

        task_categories = Counter()
        for interaction in interactions:
            task_type = interaction.get("task_type", "unknown")
            task_categories[task_type] += 1

        if task_categories:
            top_task = task_categories.most_common(1)[0]
            patterns.append(
                Pattern(
                    pattern_type="dominant_task",
                    description=f"Most frequent task type: {top_task[0]} ({top_task[1]}/{len(interactions)} times)",
                    confidence=0.85,
                )
            )

        return patterns

    def _find_repeated_phrases(self, text: str, min_words: int = 2) -> list[str]:
        """Find repeated phrases in text."""
        words = text.lower().split()
        phrases: Counter[str] = Counter()

        for length in range(min_words, min(6, len(words) // 2 + 1)):
            for i in range(len(words) - length + 1):
                phrase = " ".join(words[i : i + length])
                phrases[phrase] += 1

        return [phrase for phrase, count in phrases.items() if count > 1]

    def _autocorrelation(self, values: list[float], lag: int) -> float:
        """Compute autocorrelation at given lag."""
        n = len(values)
        if n <= lag:
            return 0.0
        mean = sum(values) / n
        numerator = sum((values[i] - mean) * (values[i - lag] - mean) for i in range(lag, n))
        denominator = sum((v - mean) ** 2 for v in values)
        return numerator / denominator if denominator != 0 else 0.0

    def _detect_temporal_patterns(
        self, interactions: list[dict[str, Any]]
    ) -> list[Pattern]:
        """Detect time-based patterns."""
        patterns: list[Pattern] = []
        timestamps = []
        for interaction in interactions:
            ts = interaction.get("timestamp")
            if ts:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(ts)
                    timestamps.append(dt)
                except (ValueError, TypeError):
                    pass

        if len(timestamps) < 3:
            return patterns

        hours = [t.hour for t in timestamps]
        hour_counts = Counter(hours)
        peak_hour = hour_counts.most_common(1)[0]
        patterns.append(
            Pattern(
                pattern_type="peak_usage_hour",
                description=f"Peak activity hour: {peak_hour[0]}:00 ({peak_hour[1]} interactions)",
                confidence=0.7,
            )
        )

        return patterns


class PredictionEngine:
    """Makes predictions based on historical data and patterns."""

    def linear_predict(self, values: list[float], steps_ahead: int = 1) -> Prediction:
        """Simple linear extrapolation."""
        n = len(values)
        if n < 2:
            return Prediction(
                target=f"Step {n + steps_ahead}",
                predicted_value=str(values[-1] if values else 0),
                confidence=0.2,
                method="linear",
            )

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        predicted = slope * (n + steps_ahead - 1) + intercept

        ss_res = sum((values[i] - (slope * i + intercept)) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return Prediction(
            target=f"Step {n + steps_ahead}",
            predicted_value=f"{predicted:.4f}",
            confidence=max(0.1, min(0.95, r_squared)),
            method="linear_regression",
            supporting_patterns=[
                f"R² = {r_squared:.3f}",
                f"Slope = {slope:.4f}",
            ],
        )

    def moving_average_predict(
        self, values: list[float], window: int = 3, steps_ahead: int = 1
    ) -> Prediction:
        """Moving average prediction."""
        if len(values) < window:
            avg = sum(values) / len(values) if values else 0
            return Prediction(
                target=f"Step {len(values) + steps_ahead}",
                predicted_value=f"{avg:.4f}",
                confidence=0.3,
                method="simple_average",
            )

        recent = values[-window:]
        avg = sum(recent) / window

        trend = (values[-1] - values[-window]) / window

        predicted = avg + trend * steps_ahead

        confidence = min(0.85, 0.4 + 0.1 * min(window, len(values)))

        return Prediction(
            target=f"Step {len(values) + steps_ahead}",
            predicted_value=f"{predicted:.4f}",
            confidence=confidence,
            method=f"moving_average(window={window})",
            supporting_patterns=[
                f"Window average: {avg:.4f}",
                f"Trend: {trend:.4f}/step",
            ],
        )

    def classify_trend(self, values: list[float]) -> str:
        """Classify the overall trend direction."""
        if len(values) < 2:
            return "insufficient_data"

        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        positive = sum(1 for d in diffs if d > 0)
        negative = sum(1 for d in diffs if d < 0)
        total = len(diffs)

        if positive / total > 0.7:
            return "strong_uptrend"
        elif positive / total > 0.55:
            return "mild_uptrend"
        elif negative / total > 0.7:
            return "strong_downtrend"
        elif negative / total > 0.55:
            return "mild_downtrend"
        else:
            return "sideways"

    def estimate_volatility(self, values: list[float]) -> float:
        """Estimate volatility (coefficient of variation)."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        std = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
        return abs(std / mean)
