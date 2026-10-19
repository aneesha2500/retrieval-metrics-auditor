"""list_runs, get_run and score_queries: the runs returned are the ones asked for, and well formed."""

from .checks import result, run_id_problem


def verify_list_input(value):
    return result(True, "input is valid")


def verify_list_output(input_value, output_value, workspace):
    ids = [run.run_id for run in output_value.runs]
    if ids != sorted(set(ids)):
        return result(False, "runs must be unique and sorted by run id")
    if any(input_value.retriever not in run.retriever for run in output_value.runs):
        return result(False, "a run does not match the retriever filter")
    return result(True, f"{len(ids)} run(s) listed")


def verify_run_input(value):
    problem = run_id_problem(value.run_id)
    return result(False, problem) if problem else result(True, "input is valid")


def verify_run_output(input_value, output_value, workspace):
    if output_value.run_id != input_value.run_id:
        return result(False, "output is for another run")
    if output_value.k < 1 or not output_value.queries:
        return result(False, "the run has no queries or no k")
    for row in output_value.queries:
        if len(row.retrieved) > output_value.k or len(set(row.retrieved)) != len(row.retrieved):
            return result(False, f"{row.query_id} retrieved more than k or a duplicate example")
        if row.latency_ms < 0:
            return result(False, f"{row.query_id} has a negative latency")
    return result(True, f"run {output_value.run_id} holds {len(output_value.queries)} queries")


def verify_scores_output(input_value, output_value, workspace):
    if output_value.run_id != input_value.run_id:
        return result(False, "output is for another run")
    if output_value.k < 1 or not output_value.queries:
        return result(False, "the run has no queries or no k")
    if len(output_value.latencies_sorted_ms) != len(output_value.queries):
        return result(False, "there must be one latency per query")
    if output_value.latencies_sorted_ms != sorted(output_value.latencies_sorted_ms):
        return result(False, "latencies_sorted_ms is not sorted ascending")
    for row in output_value.queries:
        values = (row.recall, row.precision, row.reciprocal_rank)
        if any(v < 0 or v > 1 for v in values):
            return result(False, f"{row.query_id} has a score outside 0 to 1")
        if not row.evaluated and (any(values) or row.hit):
            return result(False, f"{row.query_id} is not evaluated but has a nonzero score")
        if row.hit != (row.recall > 0):
            return result(False, f"{row.query_id} hit disagrees with its recall")
    return result(True, f"scored {len(output_value.queries)} queries of run {output_value.run_id}")
