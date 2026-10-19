from __future__ import annotations

from pathlib import Path

import pytest

from contract import ListRunsInput, RunInput
from plugin import compute_metrics, get_run, list_runs, score_queries
from plugin.runs import metrics, nearest_rank


def test_definitions_on_a_hand_worked_run() -> None:
    rows = [
        {"query_id": "q1", "retrieved": ["a", "b", "c"], "relevant": ["b", "x"], "latency_ms": 3.0},
        {"query_id": "q2", "retrieved": ["d"], "relevant": ["d"], "latency_ms": 1.0},
        {"query_id": "q3", "retrieved": [], "relevant": ["e"], "latency_ms": 2.0},
        {"query_id": "q4", "retrieved": ["f"], "relevant": [], "latency_ms": 4.0},
    ]
    m = metrics("run-99-test", 3, rows)
    assert (m.queries_total, m.queries_evaluated) == (4, 3)
    assert m.recall_at_k == round((1 / 2 + 1 + 0) / 3, 4)
    assert m.precision_at_k == round((1 / 3 + 1 / 3 + 0) / 3, 4)
    assert m.mrr == round((1 / 2 + 1 + 0) / 3, 4)
    assert m.hit_rate == round(2 / 3, 4) and m.empty_rate == 0.25
    assert (m.latency_p50_ms, m.latency_p95_ms) == (2.0, 4.0)


def test_nearest_rank() -> None:
    values = [float(v) for v in range(1, 16)]
    assert nearest_rank(values, 50) == 8.0 and nearest_rank(values, 95) == 15.0
    assert nearest_rank([5.0], 95) == 5.0


def test_tools() -> None:
    listed = list_runs(ListRunsInput(retriever=""), Path(".")).runs
    assert len(listed) == 5 and all(run.queries == 15 for run in listed)
    lsh = [r.run_id for r in list_runs(ListRunsInput(retriever="lsh"), Path(".")).runs]
    assert lsh == ["run-01-lsh-ast-t03", "run-02-lsh-ast-t05", "run-03-lsh-token-t03"]
    run = get_run(RunInput(run_id="run-04-full-scan"), Path("."))
    assert compute_metrics(RunInput(run_id=run.run_id), Path(".")).queries_total == len(run.queries)
    with pytest.raises(ValueError):
        get_run(RunInput(run_id="run-99-none"), Path("."))


@pytest.mark.parametrize("run_id", [r.run_id for r in list_runs(ListRunsInput(retriever=""), Path(".")).runs])
def test_score_queries_aggregate_to_the_reference(run_id: str) -> None:
    """Aggregating score_queries' rows as the task instructions say gives compute_metrics' values."""
    scores = score_queries(RunInput(run_id=run_id), Path("."))
    ref = compute_metrics(RunInput(run_id=run_id), Path("."))
    rows = scores.queries
    ev = [row for row in rows if row.evaluated]
    assert (len(rows), len(ev)) == (ref.queries_total, ref.queries_evaluated)
    for field, attr in (("recall_at_k", "recall"), ("precision_at_k", "precision"), ("mrr", "reciprocal_rank")):
        assert abs(round(sum(getattr(row, attr) for row in ev) / len(ev), 4) - getattr(ref, field)) <= 0.0001
    assert round(sum(row.hit for row in ev) / len(ev), 4) == ref.hit_rate
    assert round(sum(row.empty for row in rows) / len(rows), 4) == ref.empty_rate
    lat = scores.latencies_sorted_ms
    assert (lat[7], lat[14]) == (ref.latency_p50_ms, ref.latency_p95_ms)
