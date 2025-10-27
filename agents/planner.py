"""Simple rule-based task planner for SLA-Forge agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class TaskPlan:
    """Structured plan describing how the agent pipeline should process a request."""

    task_type: str
    tool_name: str
    query: str
    metadata: Dict[str, str] = field(default_factory=dict)


class Planner:
    """Rule-based planner that maps a natural-language request to an agent tool plan."""

    _TASK_RULES: List[Dict[str, Iterable[str]]] = [
        {
            "task_type": "anomaly_diagnosis",
            "tool": "anomaly_diagnosis",
            "keywords": ("告警", "报警", "异常", "诊断"),
        },
        {
            "task_type": "sop_lookup",
            "tool": "sop_lookup",
            "keywords": ("sop", "保全", "操作规程", "标准作业", "步骤", "检修"),
        },
        {
            "task_type": "workorder_recommendation",
            "tool": "workorder_recommendation",
            "keywords": ("bom", "工单", "备件", "物料", "更换", "维修任务"),
        },
    ]

    def __init__(self, default_task: str = "sop_lookup") -> None:
        self.default_task = default_task

    def __call__(self, request: str) -> TaskPlan:
        return self.plan(request)

    def plan(self, request: str) -> TaskPlan:
        """Return a :class:`TaskPlan` describing how downstream agents should act."""

        normalized = request.lower()
        for rule in self._TASK_RULES:
            matched_keywords = [kw for kw in rule["keywords"] if kw.lower() in normalized]
            if matched_keywords:
                return TaskPlan(
                    task_type=rule["task_type"],
                    tool_name=rule["tool"],
                    query=self._extract_query(request),
                    metadata={
                        "matched_keywords": ",".join(matched_keywords),
                        "priority": self._estimate_priority(request),
                    },
                )

        # Fall back to a default task so that the pipeline can still operate.
        return TaskPlan(
            task_type=self.default_task,
            tool_name=self.default_task,
            query=self._extract_query(request),
            metadata={
                "matched_keywords": "",
                "priority": self._estimate_priority(request),
                "reason": "fallback",
            },
        )

    @staticmethod
    def _extract_query(request: str) -> str:
        """Extract the part of the request that should be used as a retrieval query."""

        return request.strip()

    @staticmethod
    def _estimate_priority(request: str) -> str:
        """Infer a coarse priority hint for the scheduler based on the request wording."""

        markers = {
            "紧急": "high",
            "立即": "high",
            "尽快": "high",
            "建议": "standard",
            "优化": "standard",
        }
        normalized = request.lower()
        for marker, level in markers.items():
            if marker in normalized:
                return level
        return "standard"


__all__ = ["Planner", "TaskPlan"]
