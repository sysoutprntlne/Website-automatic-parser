# Benchmark comparison

Run type: mock-harness-only

| Configuration | Intent proxy | Unsupported flags | Relevance proxy | Style proxy | Latency (s) | Calls | Revisions | Failure rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.500 | 2.000 | 0.667 | 1.000 | 0.000 | 2.000 | 0.000 | 0.667 |
| rag | 0.500 | 2.000 | 0.667 | 1.000 | 0.006 | 2.000 | 0.000 | 0.667 |
| rag_feedback | 0.500 | 2.000 | 0.667 | 1.000 | 0.006 | 3.000 | 0.000 | 0.667 |

Mock text is fixed and does not measure model quality.
Deterministic quality checks are narrow regex/phrase proxies, not factual correctness proof.
Independent model judgments are optional heuristics; human review remains pending.
No held-out target replies are passed to generation or retrieval.

Model-based judgments: pending
Human review: pending.
