# Retrieval Metrics Auditor

A `nanoagent.plugin/v1` plugin, built with the structure of NanoAgent's
reference plugin, [arxiv-source](https://github.com/zeyuyang8/arxiv-source).
An agent audits a logged retrieval run from a code-explanation agent that
retrieves similar Python examples with MinHash-LSH. It computes the run's
retrieval-quality and latency metrics by exact definitions, and the verifier
checks every number.

## Tools

| Tool | Does | Code |
|---|---|---|
| `list_runs` | Lists the bundled runs: run id, retriever, k and number of queries (optionally filtered by retriever) | `src/plugin/runs.py` |
| `get_run` | Returns a run's queries, each with its retrieved example ids, ground-truth relevant ids and latency | `src/plugin/runs.py` |
| `score_queries` | Scores each query (evaluated, empty, recall, precision, reciprocal rank, hit) and lists the latencies sorted, so the agent aggregates instead of intersecting lists by hand | `src/plugin/runs.py` |
| `compute_metrics` | Computes the run's metrics by the definitions below; the `audit-run` reference | `src/plugin/runs.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `audit-run` | Computes a run's recall, precision, MRR, hit rate, empty rate and p50/p95 latency | `agent`, with `list_runs`, `get_run` and `score_queries`; reference `compute_metrics` |

### Metric definitions

k is the run's k (5). A query is *evaluated* when its relevant list is not
empty.

| Metric | Definition |
|---|---|
| `queries_total` | queries in the run |
| `queries_evaluated` | evaluated queries |
| `recall_at_k` | mean over evaluated queries of \|retrieved[:k] ∩ relevant\| / \|relevant\| |
| `precision_at_k` | mean over evaluated queries of \|retrieved[:k] ∩ relevant\| / k |
| `mrr` | mean over evaluated queries of 1 / rank of the first relevant retrieved example (0 if none) |
| `hit_rate` | fraction of evaluated queries with at least one relevant example retrieved |
| `empty_rate` | fraction of all queries that retrieved nothing |
| `latency_p50_ms`, `latency_p95_ms` | nearest-rank percentiles over all queries: sorted ascending, the value at 1-based position ⌈p/100 · n⌉ |

Before the agent starts, NanoAgent runs `compute_metrics` and pins its output.
`verifier/metrics.py` compares the agent's nine values with it:

- counts must match exactly;
- rates must be within 0.0005 (they are reported to 4 decimals);
- latencies must be within 0.005 ms (they are copied from the log).

`score_queries` does the per-query set work; the agent still has to apply the
run-level rules itself: average only over evaluated queries (unevaluated rows
show zeros that must be left out), count empty retrievals over all queries, and
pick the nearest-rank positions. A tool's output is checked too: one sorted
latency per query, scores between 0 and 1, and zeros on unevaluated rows.

The score is the fraction of the nine metrics that are right, and the verdict
lists each wrong one with its expected value. Metrics for another run, or a
value that is not a number, are refused.

### The data

`src/plugin/data/runs.json` holds five runs of 15 MBPP test-split queries each.
They were logged from our MinHash-LSH code-explanation project, retrieving from
the 474 non-test MBPP problems:

| Run | Retriever |
|---|---|
| `run-01-lsh-ast-t03` | AST 4-shingle LSH, Jaccard threshold 0.3 |
| `run-02-lsh-ast-t05` | AST 4-shingle LSH, Jaccard threshold 0.5 |
| `run-03-lsh-token-t03` | token 4-shingle LSH, threshold 0.3 |
| `run-04-full-scan` | exhaustive exact Jaccard |
| `run-05-random` | random examples |

A query's relevant set is the corpus examples whose exact Jaccard similarity of
AST 4-shingles with it is at least 0.4 (at most 10). Each run includes three
queries with no relevant example, which tests the evaluated-query rule. The
runs, empty retrievals included, are fixed in the file, so every run of the
task sees the same data.

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs (none)
├── src/plugin/      # the MCP server (__main__.py, IMPLEMENTATIONS), runs.py and data/runs.json
├── tests/           # test_verifier.py (correct, wrong, missing, malformed, boundary) and test_runs.py
├── ui/              # outputs drawn from their JSON Schema: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package: runs.py, metrics.py, checks.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
```

On RUSH Lab, ask the plugin's chat, for example "audit run-02-lsh-ast-t05".
