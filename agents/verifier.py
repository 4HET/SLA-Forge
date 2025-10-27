"""Simple verifier that performs rule-based sanity checks on solver outputs."""
from __future__ import annotations

from dataclasses import dataclass

from .planner import TaskPlan
from .solver import SolveResult
from .tools import RetrievalResult


@dataclass
class VerificationResult:
    """Outcome of the verification stage."""

    passed: bool
    answer: str
    feedback: str
    confidence: float


class Verifier:
    """Perform minimal consistency checks before returning the agent answer."""

    def verify(
        self,
        plan: TaskPlan,
        solve_result: SolveResult,
        retrieval: RetrievalResult,
    ) -> VerificationResult:
        has_context = bool(retrieval.context)
        answer_ok = bool(solve_result.answer.strip())
        passed = has_context and answer_ok

        if passed:
            feedback = "通过校验"
        elif not has_context:
            feedback = "缺少检索上下文，建议人工复核"
        else:
            feedback = "生成内容为空，建议重试"

        confidence = retrieval.score if retrieval.score else (0.2 if passed else 0.0)
        return VerificationResult(
            passed=passed,
            answer=solve_result.answer,
            feedback=feedback,
            confidence=round(confidence, 2),
        )


__all__ = ["Verifier", "VerificationResult"]
