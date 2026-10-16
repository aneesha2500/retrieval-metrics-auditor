"""Checks shared by the tool verifiers. Pure functions of their arguments."""

import re

RUN_ID = re.compile(r"^run-\d{2}-[a-z0-9-]+$")
RATE_TOLERANCE = 0.0005  # rates are reported to 4 decimals
LATENCY_TOLERANCE = 0.005  # latencies are copied from the run, which gives 2 decimals
RATES = ("recall_at_k", "precision_at_k", "mrr", "hit_rate", "empty_rate")
LATENCIES = ("latency_p50_ms", "latency_p95_ms")
COUNTS = ("queries_total", "queries_evaluated")


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def run_id_problem(run_id):
    return None if RUN_ID.fullmatch(run_id) else f"{run_id!r} is not a run id like run-01-lsh-ast-t03"


def fields(metrics):
    """A contract MetricsOutput as a plain mapping of its metric fields."""
    return {
        "queries_total": metrics.queries_total,
        "queries_evaluated": metrics.queries_evaluated,
        "recall_at_k": metrics.recall_at_k,
        "precision_at_k": metrics.precision_at_k,
        "mrr": metrics.mrr,
        "hit_rate": metrics.hit_rate,
        "empty_rate": metrics.empty_rate,
        "latency_p50_ms": metrics.latency_p50_ms,
        "latency_p95_ms": metrics.latency_p95_ms,
    }
