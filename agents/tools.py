"""Lightweight retrieval tool implementations used by the agent pipeline."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .planner import TaskPlan


@dataclass
class RetrievalResult:
    """Container for retrieved context used by downstream agent stages."""

    task_type: str
    query: str
    context: str
    source: str
    score: float
    metadata: Dict[str, str] = field(default_factory=dict)


class ToolExecutor:
    """Load small demo corpora and provide simple similarity-based retrieval."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        if data_root is None:
            data_root = Path(__file__).resolve().parents[1] / "project" / "data"
        self.data_root = data_root

        self._anomaly_entries = self._load_anomaly_corpus()
        self._sop_entries = self._load_sop_corpus()
        self._bom_entries = self._load_bom_corpus()

    def execute(self, plan: TaskPlan) -> RetrievalResult:
        """Execute the tool indicated by ``plan`` and return retrieved context."""

        tool = plan.tool_name
        if tool == "anomaly_diagnosis":
            return self._run_anomaly_tool(plan)
        if tool == "sop_lookup":
            return self._run_sop_tool(plan)
        if tool == "workorder_recommendation":
            return self._run_bom_tool(plan)
        return RetrievalResult(
            task_type=plan.task_type,
            query=plan.query,
            context="",
            source="unknown",
            score=0.0,
            metadata={"error": f"no tool named {tool}"},
        )

    # ------------------------------------------------------------------
    # Data loading helpers
    def _load_anomaly_corpus(self) -> List[Dict[str, str]]:
        path = self.data_root / "anomaly_diagnostics.csv"
        return self._load_csv(path)

    def _load_sop_corpus(self) -> List[Dict[str, str]]:
        path = self.data_root / "sop_lookup.csv"
        return self._load_csv(path)

    def _load_bom_corpus(self) -> List[Dict[str, str]]:
        path = self.data_root / "bom_workorders.txt"
        if not path.exists():
            return []
        entries: List[Dict[str, str]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = [part.strip() for part in stripped.split("|")]
            if len(parts) < 4:
                continue
            work_order = parts[2].split(":", 1)[-1].strip()
            advice = parts[3].split(":", 1)[-1].strip() if len(parts) >= 4 else ""
            entries.append(
                {
                    "asset": parts[0],
                    "issue": parts[1],
                    "work_order": work_order,
                    "advice": advice,
                }
            )
        return entries

    def _load_csv(self, path: Path) -> List[Dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]

    # ------------------------------------------------------------------
    # Tool implementations
    def _run_anomaly_tool(self, plan: TaskPlan) -> RetrievalResult:
        entry, score = self._best_match(self._anomaly_entries, plan.query, fields=("symptom", "probable_causes"))
        if entry is None:
            return self._empty_result(plan)
        context = (
            f"告警 {entry['alert_id']}：{entry['symptom']}\n"
            f"可能原因：{entry['probable_causes']}\n"
            f"推荐措施：{entry['recommended_actions']}"
        )
        return RetrievalResult(
            task_type=plan.task_type,
            query=plan.query,
            context=context,
            source=f"anomaly_diagnostics.csv#{entry['alert_id']}",
            score=score,
            metadata={"alert_id": entry["alert_id"]},
        )

    def _run_sop_tool(self, plan: TaskPlan) -> RetrievalResult:
        entry, score = self._best_match(self._sop_entries, plan.query, fields=("equipment", "issue"))
        if entry is None:
            return self._empty_result(plan)
        context = (
            f"设备 {entry['equipment']} 的问题：{entry['issue']}\n"
            f"SOP 步骤：{entry['sop_steps']}"
        )
        return RetrievalResult(
            task_type=plan.task_type,
            query=plan.query,
            context=context,
            source=f"sop_lookup.csv#{entry['equipment']}",
            score=score,
            metadata={"equipment": entry["equipment"]},
        )

    def _run_bom_tool(self, plan: TaskPlan) -> RetrievalResult:
        entry, score = self._best_match(self._bom_entries, plan.query, fields=("asset", "issue"))
        if entry is None:
            return self._empty_result(plan)
        context = (
            f"单元 {entry['asset']} 的问题：{entry['issue']}\n"
            f"建议工单：{entry['work_order']}\n"
            f"执行建议：{entry['advice']}"
        )
        return RetrievalResult(
            task_type=plan.task_type,
            query=plan.query,
            context=context,
            source=f"bom_workorders.txt#{entry['asset']}",
            score=score,
            metadata={"asset": entry["asset"], "work_order": entry["work_order"]},
        )

    # ------------------------------------------------------------------
    # Utility helpers
    def _best_match(
        self,
        entries: Iterable[Dict[str, str]],
        query: str,
        fields: Iterable[str],
    ) -> tuple[Optional[Dict[str, str]], float]:
        best_entry: Optional[Dict[str, str]] = None
        best_score = 0.0
        for entry in entries:
            text = " ".join(entry[field] for field in fields if field in entry)
            score = self._score(query, text)
            if score > best_score:
                best_entry = entry
                best_score = score
        return best_entry, best_score

    @staticmethod
    def _score(query: str, text: str) -> float:
        if not query or not text:
            return 0.0
        return SequenceMatcher(None, query.lower(), text.lower()).ratio()

    def _empty_result(self, plan: TaskPlan) -> RetrievalResult:
        return RetrievalResult(
            task_type=plan.task_type,
            query=plan.query,
            context="",
            source="",
            score=0.0,
            metadata={"warning": "no matching entry"},
        )


__all__ = ["ToolExecutor", "RetrievalResult"]
