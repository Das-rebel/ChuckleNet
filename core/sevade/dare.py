"""Light-weight DARE support used by the autonomous orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(slots=True)
class HypothesisCandidate:
    """Ranked hypothesis emitted by DARE."""

    focus_area: str
    score: float
    rationale: str


class DynamicAgentiveReasoningEngine:
    """Produce ranked hypotheses from issue signals."""

    def generate(self, issues: Iterable[str]) -> List[HypothesisCandidate]:
        ranked: List[HypothesisCandidate] = []
        for issue in issues:
            focus = issue.replace("_", " ")
            if "memory" in issue:
                score = 0.95
            elif "overfit" in issue:
                score = 0.8
            else:
                score = 0.6
            ranked.append(
                HypothesisCandidate(
                    focus_area=focus,
                    score=score,
                    rationale=f"Prioritize {focus} based on the latest failure signals.",
                )
            )
        return sorted(ranked, key=lambda item: item.score, reverse=True)

    def summarize(self, analysis: Dict[str, object]) -> Dict[str, object]:
        issues = analysis.get("issues", [])
        candidates = self.generate(issues if isinstance(issues, list) else [])
        best = candidates[0] if candidates else HypothesisCandidate("stability", 0.5, "Fallback.")
        return {
            "focus_area": best.focus_area,
            "priority": best.score,
            "rationale": best.rationale,
            "candidate_count": len(candidates),
        }

