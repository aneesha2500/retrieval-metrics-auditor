"""Each tool's and task's typed input and output (see nanoagent.plugin.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    LIST_RUNS = "list_runs"
    GET_RUN = "get_run"
    SCORE_QUERIES = "score_queries"
    COMPUTE_METRICS = "compute_metrics"


class Task(Enum):
    AUDIT_RUN = "audit-run"


RUN_ID = "A run id, as list_runs gives it, e.g. run-01-lsh-ast-t03"
RATE = "A mean or fraction between 0 and 1, rounded to 4 decimals"
LATENCY = "Milliseconds, exactly one of the run's latency_ms values (nearest-rank percentile)"


@dataclass
class ListRunsInput(Output):
    retriever: Annotated[str, "Only runs whose retriever name contains this text; empty for every run"]


@dataclass
class RunSummary(Output):
    run_id: Annotated[str, RUN_ID]
    retriever: Annotated[str, "The retriever the run used"]
    k: Annotated[int, "How many examples each query asked for"]
    queries: Annotated[int, "How many queries the run holds"]


@dataclass
class ListRunsOutput(Output):
    runs: Annotated[list[RunSummary], "The matching runs, by run id"]


@dataclass
class QueryRow(Output):
    query_id: Annotated[str, "The MBPP query problem, e.g. mbpp-17"]
    retrieved: Annotated[list[str], "The example ids the retriever returned, best first (at most k, may be empty)"]
    relevant: Annotated[list[str], "The ground-truth relevant example ids (may be empty)"]
    latency_ms: Annotated[float, "The retrieval's latency in milliseconds"]


@dataclass
class RunInput(Output):
    run_id: Annotated[str, RUN_ID]


@dataclass
class RunOutput(Output):
    run_id: Annotated[str, RUN_ID]
    retriever: Annotated[str, "The retriever the run used"]
    k: Annotated[int, "How many examples each query asked for"]
    queries: Annotated[list[QueryRow], "Every query in the run"]


@dataclass
class QueryScore(Output):
    query_id: Annotated[str, "The MBPP query problem, e.g. mbpp-17"]
    evaluated: Annotated[bool, "Whether the query has at least one relevant example"]
    empty: Annotated[bool, "Whether the query retrieved nothing"]
    recall: Annotated[float, "|retrieved[:k] ∩ relevant| / |relevant|, to 6 decimals (0 when not evaluated)"]
    precision: Annotated[float, "|retrieved[:k] ∩ relevant| / k, to 6 decimals (0 when not evaluated)"]
    reciprocal_rank: Annotated[
        float, "1 / rank of the first relevant retrieved example, to 6 decimals (0 when none, or not evaluated)"
    ]
    hit: Annotated[bool, "Whether at least one relevant example was retrieved"]


@dataclass
class ScoresOutput(Output):
    run_id: Annotated[str, RUN_ID]
    k: Annotated[int, "How many examples each query asked for"]
    queries: Annotated[list[QueryScore], "One score row per query, in the run's order"]
    latencies_sorted_ms: Annotated[list[float], "Every query's latency_ms, sorted ascending"]


@dataclass
class MetricsOutput(Output):
    run_id: Annotated[str, RUN_ID]
    queries_total: Annotated[int, "How many queries the run holds"]
    queries_evaluated: Annotated[int, "How many queries have at least one relevant example"]
    recall_at_k: Annotated[float, RATE]
    precision_at_k: Annotated[float, RATE]
    mrr: Annotated[float, RATE]
    hit_rate: Annotated[float, RATE]
    empty_rate: Annotated[float, RATE]
    latency_p50_ms: Annotated[float, LATENCY]
    latency_p95_ms: Annotated[float, LATENCY]


TOOLS = {
    Tool.LIST_RUNS: (ListRunsInput, ListRunsOutput),
    Tool.GET_RUN: (RunInput, RunOutput),
    Tool.SCORE_QUERIES: (RunInput, ScoresOutput),
    Tool.COMPUTE_METRICS: (RunInput, MetricsOutput),
}
TASKS = {Task.AUDIT_RUN: (RunInput, MetricsOutput)}
