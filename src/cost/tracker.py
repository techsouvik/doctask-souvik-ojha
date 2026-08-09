"""Cost & Latency Tracking Module."""

import time
from typing import Dict
from src.models.domain import NodeUsage, RunCostReport


class CostTracker:
    def __init__(self, run_id: str, project_id: str):
        self.run_id = run_id
        self.project_id = project_id
        self.report = RunCostReport(run_id=run_id, project_id=project_id)
        self.start_time = time.time()

    def record_node_execution(
        self,
        node_name: str,
        duration_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0
    ):
        if node_name not in self.report.node_breakdown:
            self.report.node_breakdown[node_name] = NodeUsage(node_name=node_name)

        usage = self.report.node_breakdown[node_name]
        usage.calls_count += 1
        usage.total_tokens_in += tokens_in
        usage.total_tokens_out += tokens_out
        usage.cost_usd += cost_usd
        usage.duration_ms += duration_ms

        self.report.total_cost_usd += cost_usd

    def get_summary(self) -> RunCostReport:
        self.report.total_duration_ms = (time.time() - self.start_time) * 1000.0
        return self.report
