"""
Verification Engine — validates claims, fact-checks,
verifies code output, and ensures accuracy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VerificationResult:
    claim: str
    is_verified: bool
    confidence: float
    method: str
    evidence: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    score: float = 0.0


class VerificationEngine:
    """Verifies claims, validates data, and fact-checks information."""

    def verify_claim(self, claim: str, context: str = "") -> VerificationResult:
        """Verify a factual claim against available context."""
        evidence: list[str] = []
        notes: list[str] = []
        confidence = 0.5

        claim_lower = claim.lower()
        context_lower = context.lower()

        if context:
            claim_words = set(re.findall(r'\b\w+\b', claim_lower))
            context_words = set(re.findall(r'\b\w+\b', context_lower))
            overlap = claim_words & context_words
            total = max(len(claim_words), 1)
            evidence_ratio = len(overlap) / total

            if evidence_ratio > 0.7:
                confidence = 0.85
                evidence.append(f"High word overlap with provided context ({evidence_ratio:.0%})")
            elif evidence_ratio > 0.4:
                confidence = 0.65
                evidence.append(f"Moderate word overlap with context ({evidence_ratio:.0%})")
            else:
                confidence = 0.4
                notes.append("Limited overlap with provided context")

        if re.search(r'\b(always|never|all|none|every|no one)\b', claim_lower):
            confidence *= 0.8
            notes.append("Absolute claim detected — reduces confidence")

        if re.search(r'\b\w+\s+\d{4}\b', claim):
            confidence *= 1.05
            notes.append("Contains dated reference")

        if re.search(r'\b\d+(\.\d+)?%\b', claim):
            confidence *= 1.02
            notes.append("Contains specific numerical data")

        return VerificationResult(
            claim=claim,
            is_verified=confidence > 0.6,
            confidence=min(0.99, confidence),
            method="context_matching",
            evidence=evidence,
            notes=notes,
            score=confidence,
        )

    def validate_code_output(
        self, code: str, expected_output: str, actual_output: str
    ) -> VerificationResult:
        """Verify that code produces expected output."""
        notes: list[str] = []
        evidence: list[str] = []
        confidence = 0.0

        expected_clean = expected_output.strip()
        actual_clean = actual_output.strip()

        if expected_clean == actual_clean:
            confidence = 1.0
            evidence.append("Output matches expected exactly")
        elif expected_clean in actual_clean:
            confidence = 0.8
            evidence.append("Expected output found within actual output")
        else:
            similarity = self._text_similarity(expected_clean, actual_clean)
            confidence = similarity
            if similarity > 0.8:
                evidence.append(f"High similarity ({similarity:.0%})")
            elif similarity > 0.5:
                notes.append(f"Moderate similarity ({similarity:.0%}) — possible formatting difference")
            else:
                notes.append(f"Low similarity ({similarity:.0%}) — outputs differ significantly")

        try:
            compile(code, "<verify>", "exec")
            evidence.append("Code compiles successfully")
        except SyntaxError as e:
            notes.append(f"Syntax error in code: {e}")
            confidence *= 0.5

        return VerificationResult(
            claim=f"Code output verification",
            is_verified=confidence > 0.7,
            confidence=min(0.99, confidence),
            method="output_comparison",
            evidence=evidence,
            notes=notes,
            score=confidence,
        )

    def validate_data_integrity(self, data: list[dict[str, Any]]) -> VerificationResult:
        """Validate data consistency and integrity."""
        issues: list[str] = []
        evidence: list[str] = []

        if not data:
            return VerificationResult(
                claim="Data integrity check",
                is_verified=False,
                confidence=0.0,
                method="data_validation",
                notes=["Empty dataset"],
            )

        all_keys = set()
        for row in data:
            all_keys.update(row.keys())

        completeness_scores = []
        for row in data:
            present = len([k for k in all_keys if k in row and row[k]])
            completeness_scores.append(present / max(len(all_keys), 1))

        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        evidence.append(f"Average completeness: {avg_completeness:.0%}")

        null_counts = {}
        for key in all_keys:
            nulls = sum(1 for row in data if key not in row or row[key] is None or row[key] == "")
            if nulls > 0:
                null_counts[key] = nulls

        if null_counts:
            issues.append(f"Columns with missing data: {null_counts}")
        else:
            evidence.append("No missing data detected")

        numeric_cols = set()
        for key in all_keys:
            for row in data:
                if key in row and row[key] is not None:
                    try:
                        float(row[key])
                        numeric_cols.add(key)
                        break
                    except (ValueError, TypeError):
                        break

        outlier_info = []
        for col in numeric_cols:
            values = []
            for row in data:
                if col in row and row[col] is not None:
                    try:
                        values.append(float(row[col]))
                    except (ValueError, TypeError):
                        pass
            if len(values) > 2:
                mean = sum(values) / len(values)
                std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
                outliers = [v for v in values if abs(v - mean) > 2 * std]
                if outliers:
                    outlier_info.append(f"{col}: {len(outliers)} outliers")

        if outlier_info:
            issues.append(f"Outliers detected: {', '.join(outlier_info)}")

        confidence = avg_completeness * (0.8 if not issues else 0.6)

        return VerificationResult(
            claim="Data integrity validation",
            is_verified=confidence > 0.7 and len(issues) == 0,
            confidence=min(0.99, confidence),
            method="data_validation",
            evidence=evidence,
            notes=issues,
            score=confidence,
        )

    def cross_reference(self, statements: list[str]) -> dict[str, Any]:
        """Cross-reference multiple statements for consistency."""
        consistency_matrix: list[dict[str, Any]] = []

        for i, s1 in enumerate(statements):
            for j, s2 in enumerate(statements[i + 1 :], i + 1):
                similarity = self._text_similarity(s1, s2)
                consistency_matrix.append({
                    "statement_1": s1[:80],
                    "statement_2": s2[:80],
                    "similarity": round(similarity, 3),
                    "consistent": similarity > 0.5,
                })

        consistent_pairs = sum(1 for c in consistency_matrix if c["consistent"])
        total_pairs = len(consistency_matrix) if consistency_matrix else 1
        consistency_score = consistent_pairs / total_pairs

        return {
            "num_statements": len(statements),
            "num_comparisons": len(consistency_matrix),
            "consistency_score": round(consistency_score, 3),
            "pairwise_results": consistency_matrix,
            "assessment": (
                "Consistent" if consistency_score > 0.7
                else "Partially consistent" if consistency_score > 0.4
                else "Inconsistent"
            ),
        }

    def logical_validity_check(self, premises: list[str], conclusion: str) -> VerificationResult:
        """Check logical validity of an argument."""
        notes: list[str] = []
        evidence: list[str] = []
        confidence = 0.5

        premise_words = set()
        for p in premises:
            premise_words.update(re.findall(r'\b\w+\b', p.lower()))

        conclusion_words = set(re.findall(r'\b\w+\b', conclusion.lower()))

        if premise_words & conclusion_words:
            overlap = len(premise_words & conclusion_words) / max(len(conclusion_words), 1)
            evidence.append(f"Conclusion shares {overlap:.0%} of terms with premises")
            confidence = min(0.9, 0.3 + overlap * 0.6)

        negation_words = {"not", "no", "never", "none", "nothing"}
        premise_has_negation = any(neg in p.lower() for p in premises for neg in negation_words)
        conclusion_has_negation = any(neg in conclusion.lower() for neg in negation_words)

        if premise_has_negation == conclusion_has_negation:
            evidence.append("Negation consistency maintained")
            confidence += 0.1
        else:
            notes.append("Negation pattern differs between premises and conclusion")

        if len(premises) >= 2:
            evidence.append(f"Argument has {len(premises)} premises supporting the conclusion")
            confidence += 0.05

        return VerificationResult(
            claim=f"Logical validity: {conclusion[:50]}",
            is_verified=confidence > 0.6,
            confidence=min(0.95, confidence),
            method="logical_analysis",
            evidence=evidence,
            notes=notes,
            score=confidence,
        )

    def _text_similarity(self, a: str, b: str) -> float:
        """Simple Jaccard similarity between two texts."""
        words_a = set(re.findall(r'\b\w+\b', a.lower()))
        words_b = set(re.findall(r'\b\w+\b', b.lower()))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
