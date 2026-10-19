"""compute_metrics (the audit-run reference) and the audit-run task's outcome check.

The agent's metrics are compared, field by field, with the ones the reference tool computed from
the same run, pinned before the agent started: counts exactly, rates within 0.0005 (they are
reported to 4 decimals) and latencies within 0.005 ms. The score is the fraction of the nine
fields that are right; the task is valid only when all are.
"""

import math

from .checks import COUNTS, LATENCY_TOLERANCE, RATE_TOLERANCE, RATES, fields, result, run_id_problem


def verify_input(value):
    problem = run_id_problem(value.run_id)
    return result(False, problem) if problem else result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    if output_value.run_id != input_value.run_id:
        return result(False, "metrics are for another run")
    values = fields(output_value)
    if not 0 <= output_value.queries_evaluated <= output_value.queries_total or output_value.queries_total < 1:
        return result(False, "query counts are inconsistent")
    for name in RATES:
        if not math.isfinite(values[name]) or not 0 <= values[name] <= 1:
            return result(False, f"{name} must be between 0 and 1")
    if output_value.latency_p50_ms > output_value.latency_p95_ms:
        return result(False, "the 50th percentile latency exceeds the 95th")
    return result(True, "metrics are well formed")


def _right(name, got, want):
    if not math.isfinite(got):
        return False
    if name in COUNTS:
        return got == want
    tolerance = RATE_TOLERANCE if name in RATES else LATENCY_TOLERANCE
    return abs(got - want) <= tolerance + 1e-12


def verify_task(arguments, output, reference, workspace):
    """``output`` and ``reference``: contract MetricsOutputs for ``arguments.run_id``."""
    if output.run_id != arguments.run_id:
        return result(False, f"the metrics are for {output.run_id}, not {arguments.run_id}", score=0.0)
    got, want = fields(output), fields(reference)
    wrong = {
        name: {"submitted": got[name], "expected": want[name]}
        for name in want
        if not _right(name, got[name], want[name])
    }
    score = (len(want) - len(wrong)) / len(want)
    if wrong:
        return result(False, f"{len(wrong)} of {len(want)} metric(s) are wrong", score=score, wrong=wrong)
    return result(True, f"all {len(want)} metrics match", score=1.0)
