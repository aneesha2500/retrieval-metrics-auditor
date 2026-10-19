from __future__ import annotations

from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import MetricsOutput, RunInput
from plugin import compute_metrics

RUN = "run-01-lsh-ast-t03"


def reference(run_id: str = RUN) -> MetricsOutput:
    return build_output(plain_output(compute_metrics(RunInput(run_id=run_id), Path("."))), MetricsOutput)


def verify(changes: dict | None = None, run_id: str = RUN) -> dict:
    output = plain_output(reference()) | (changes or {})
    return verifier.verify_task(
        "audit-run",
        build_output({"run_id": run_id}, RunInput),
        build_output(output, MetricsOutput),
        reference(run_id),
        ".",
    )


def test_approves_exact_metrics() -> None:
    verdict = verify()
    assert verdict["valid"] is True and verdict["score"] == 1.0


def test_accepts_rounding_within_half_a_unit_of_the_fourth_decimal() -> None:
    assert verify({"recall_at_k": reference().recall_at_k + 0.0004})["valid"] is True
    assert verify({"recall_at_k": reference().recall_at_k + 0.0006})["valid"] is False


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"recall_at_k": 0.9}, "recall_at_k"),
        ({"precision_at_k": 0.6}, "precision_at_k"),  # e.g. dividing by the number retrieved, not k
        ({"mrr": 0.5}, "mrr"),
        ({"hit_rate": 0.8}, "hit_rate"),
        ({"empty_rate": 0.0}, "empty_rate"),
        ({"queries_evaluated": 15}, "queries_evaluated"),  # counted queries with no relevant example
        ({"latency_p95_ms": 0.9}, "latency_p95_ms"),  # interpolated instead of nearest-rank
    ],
)
def test_refuses_each_wrong_metric_with_partial_score(changes: dict, field: str) -> None:
    verdict = verify(changes)
    assert verdict["valid"] is False and list(verdict["details"]["wrong"]) == [field]
    assert verdict["score"] == pytest.approx(8 / 9)


def test_refuses_metrics_for_another_run() -> None:
    verdict = verify({"run_id": "run-02-lsh-ast-t05"})
    assert verdict["valid"] is False and verdict["score"] == 0.0


def test_refuses_not_a_number() -> None:
    verdict = verify({"mrr": float("nan")})
    assert verdict["valid"] is False and "mrr" in verdict["details"]["wrong"]


@pytest.mark.parametrize(("run_id", "valid"), [(RUN, True), ("run-1", False), ("", False), ("RUN-01-X", False)])
def test_checks_the_run_id(run_id: str, valid: bool) -> None:
    assert verifier.verify_input("get_run", build_output({"run_id": run_id}, RunInput))["valid"] is valid


def test_checks_reference_output_is_well_formed() -> None:
    good = reference()
    assert verifier.verify_output("compute_metrics", RunInput(run_id=RUN), good, ".")["valid"] is True
    bad = build_output(plain_output(good) | {"hit_rate": 1.5}, MetricsOutput)
    assert verifier.verify_output("compute_metrics", RunInput(run_id=RUN), bad, ".")["valid"] is False


def test_score_queries_output_checks() -> None:
    from contract import ScoresOutput
    from plugin import score_queries

    given = RunInput(run_id=RUN)
    good = score_queries(given, Path("."))
    assert verifier.verify_output("score_queries", given, good, ".")["valid"] is True
    data = plain_output(good)
    unsorted = data | {"latencies_sorted_ms": list(reversed(data["latencies_sorted_ms"]))}
    assert verifier.verify_output("score_queries", given, build_output(unsorted, ScoresOutput), ".")["valid"] is False
    rows = [dict(row) for row in data["queries"]]
    idle = next(row for row in rows if not row["evaluated"])
    idle["recall"] = 0.5
    bad = data | {"queries": rows}
    assert verifier.verify_output("score_queries", given, build_output(bad, ScoresOutput), ".")["valid"] is False
    other = data | {"run_id": "run-02-lsh-ast-t05"}
    assert verifier.verify_output("score_queries", given, build_output(other, ScoresOutput), ".")["valid"] is False
