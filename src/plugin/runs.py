"""The bundled retrieval runs, and the metric definitions the audit-run task asks for.

Definitions (k is the run's k; "evaluated" queries are those with at least one relevant example):

- queries_evaluated: the number of evaluated queries.
- recall_at_k: mean over evaluated queries of |retrieved[:k] ∩ relevant| / |relevant|.
- precision_at_k: mean over evaluated queries of |retrieved[:k] ∩ relevant| / k (k even when fewer
  were retrieved).
- mrr: mean over evaluated queries of 1 / (rank of the first relevant retrieved example), 0 when none.
- hit_rate: fraction of evaluated queries with at least one relevant example retrieved.
- empty_rate: fraction of all queries that retrieved nothing.
- latency_p50_ms / latency_p95_ms: nearest-rank percentiles over all queries: sort the latencies
  ascending and take the value at position ceil(p / 100 * n) (1-based).

Rates are rounded to 4 decimals; with no evaluated queries the evaluated means are 0.
"""

from __future__ import annotations

import json
import math
from functools import cache
from pathlib import Path

from contract import (
    ListRunsInput,
    ListRunsOutput,
    MetricsOutput,
    QueryRow,
    RunInput,
    RunOutput,
    RunSummary,
)

DATA = Path(__file__).with_name("data") / "runs.json"


@cache
def runs() -> dict[str, dict]:
    return {run["run_id"]: run for run in json.loads(DATA.read_text(encoding="utf-8"))["runs"]}


def run(run_id: str) -> dict:
    if run_id not in runs():
        raise ValueError(f"unknown run_id {run_id!r}; list_runs gives the run ids")
    return runs()[run_id]


def list_runs(given: ListRunsInput, workspace: Path) -> ListRunsOutput:
    return ListRunsOutput(
        runs=[
            RunSummary(run_id=r["run_id"], retriever=r["retriever"], k=r["k"], queries=len(r["queries"]))
            for r in sorted(runs().values(), key=lambda r: r["run_id"])
            if given.retriever in r["retriever"]
        ]
    )


def get_run(given: RunInput, workspace: Path) -> RunOutput:
    r = run(given.run_id)
    return RunOutput(
        run_id=r["run_id"],
        retriever=r["retriever"],
        k=r["k"],
        queries=[QueryRow(**row) for row in r["queries"]],
    )


def nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    return ordered[max(1, math.ceil(percentile / 100 * len(ordered))) - 1]


def metrics(run_id: str, k: int, rows: list[dict]) -> MetricsOutput:
    evaluated = [row for row in rows if row["relevant"]]
    recalls, precisions, reciprocal, hits = [], [], [], []
    for row in evaluated:
        top, relevant = row["retrieved"][:k], set(row["relevant"])
        found = len(set(top) & relevant)
        recalls.append(found / len(relevant))
        precisions.append(found / k)
        rank = next((i for i, example in enumerate(top, 1) if example in relevant), None)
        reciprocal.append(1 / rank if rank else 0.0)
        hits.append(1.0 if found else 0.0)

    def mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    latencies = [row["latency_ms"] for row in rows]
    return MetricsOutput(
        run_id=run_id,
        queries_total=len(rows),
        queries_evaluated=len(evaluated),
        recall_at_k=mean(recalls),
        precision_at_k=mean(precisions),
        mrr=mean(reciprocal),
        hit_rate=mean(hits),
        empty_rate=round(sum(1 for row in rows if not row["retrieved"]) / len(rows), 4),
        latency_p50_ms=nearest_rank(latencies, 50),
        latency_p95_ms=nearest_rank(latencies, 95),
    )


def compute_metrics(given: RunInput, workspace: Path) -> MetricsOutput:
    """The audit-run reference: the metrics computed by the definitions above."""
    r = run(given.run_id)
    return metrics(r["run_id"], r["k"], r["queries"])
