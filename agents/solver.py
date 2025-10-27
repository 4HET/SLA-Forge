"""Lightweight solver that simulates downstream LLM reasoning."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from .planner import TaskPlan
from .tools import RetrievalResult


@dataclass
class SolveResult:
    """Generated answer and attribution metadata."""

    answer: str
    plan: TaskPlan
    references: Dict[str, str] = field(default_factory=dict)
    reasoning: str = ""


class Solver:
    """Compose templated responses using retrieved context."""

    def solve(self, plan: TaskPlan, retrieval: RetrievalResult) -> SolveResult:
        if not retrieval.context:
            answer = "未检索到相关知识，请转人工或补充更多信息。"
            references = {}
        else:
            answer = self._compose_answer(plan.task_type, retrieval)
            references = {"source": retrieval.source, "score": f"{retrieval.score:.2f}"}
            references.update(retrieval.metadata)

        reasoning = f"tool={plan.tool_name}; priority={plan.metadata.get('priority', 'standard')}"
        return SolveResult(answer=answer, plan=plan, references=references, reasoning=reasoning)

    def _compose_answer(self, task_type: str, retrieval: RetrievalResult) -> str:
        context = retrieval.context
        if task_type == "anomaly_diagnosis":
            return (
                "【告警诊断结果】\n"
                f"- 诊断要点：{context}\n"
                "- 请按照推荐措施执行，并记录处理结果用于后续追踪。"
            )
        if task_type == "sop_lookup":
            return (
                "【SOP 建议】\n"
                f"- 检索结果：{context}\n"
                "- 请严格对照 SOP 步骤执行，并在执行单上完成签字确认。"
            )
        if task_type == "workorder_recommendation":
            return (
                "【工单推荐】\n"
                f"- 推荐依据：{context}\n"
                "- 若需停机，请提前与生产协调确认窗口。"
            )
        return (
            "【通用响应】\n"
            f"- 参考信息：{context}\n"
            "- 建议复核需求类型以获取更准确建议。"
        )


__all__ = ["Solver", "SolveResult"]
