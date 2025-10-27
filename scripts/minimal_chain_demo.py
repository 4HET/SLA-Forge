"""Demonstrate the minimal Planner→Solver→Verifier chain on sample requests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.planner import Planner
from agents.solver import Solver
from agents.tools import ToolExecutor
from agents.verifier import Verifier


def run_request(request: str) -> None:
    planner = Planner()
    tools = ToolExecutor()
    solver = Solver()
    verifier = Verifier()

    plan = planner.plan(request)
    retrieval = tools.execute(plan)
    solve_result = solver.solve(plan, retrieval)
    verification = verifier.verify(plan, solve_result, retrieval)

    print("== 请求 ==")
    print(request)
    print("== 规划 ==")
    print(plan)
    print("== 检索上下文 ==")
    print(retrieval.context or "<无>")
    print("== 生成结果 ==")
    print(solve_result.answer)
    print("== 校验 ==")
    print(verification)
    print("\n")


if __name__ == "__main__":
    SAMPLE_REQUESTS = [
        "冲压线告警提示伺服电机振动异常，给个诊断建议",
        "SOP 查询：注塑机-03 保压阶段压力不足该如何处理",
        "BOM 显示 Line-Assembly-02 夹具气缸漏气，推荐工单",
    ]
    for req in SAMPLE_REQUESTS:
        run_request(req)
