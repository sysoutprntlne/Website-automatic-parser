# Final comparison JSON

Every completed benchmark CLI run now automatically writes `comparison.json` next
to `results.json` and `report.md`. Existing live progress output is unchanged.
No additional model requests or dependencies are needed.

```bash
# Verify with synthetic mock services
.venv/bin/python -m src.benchmarks.sample --output benchmark-results/comparison-demo
# Use your configured local generator and evaluator models
.venv/bin/python -m src.benchmarks.sample --real --repeats 3 --output benchmark-results/real
```

The terminal prints the comparison file's location after completion. The file is
UTF-8 JSON, written through a temporary file and atomically replaced. A fresh
interrupted run does not create it. If you reuse an output directory, an earlier
comparison can still exist: compare its `run_id` with the current progress/run ID.
Use distinct output directories for experiments you want to retain.

## File contents

- `schema_version`: currently 1.
- Run metadata: ID, mock/real label, completion status, timestamp, fixture hash,
  model/configuration settings and repeat count. The ID matches `results.json`.
- `configurations`: baseline, RAG and RAG with feedback. Each includes trial count
  and per-metric means, observation/missing counts, units and preferred direction.
- `comparisons`: RAG versus baseline; RAG with feedback versus baseline; and RAG
  with feedback versus RAG.
- `interpretation`: calculation definitions and limitations, explicitly marking
  statistical significance as `not_tested` and leaving `overall_winner` null.

Each comparison matches the same `(case, repeat)` between reference and candidate.
For each metric, pairs missing either value are excluded, with coverage reported:

- `reference_mean` / `candidate_mean`: means over available matched pairs, which
  can differ from full-configuration means when measurements are missing.
- `delta`: candidate minus reference. A latency delta of -2 means two seconds less.
- `percent_change`: `100 * delta / abs(reference_mean)`; null when the reference
  is zero or missing. A change from 10 seconds to 5 seconds is -50 percent.
- `percentage_point_change`: for rates only. A rate from 0.50 to 0.75 is +25
  percentage points, whereas its relative percent change is +50 percent.
- `paired_observations` / `missing_metric_pairs`: measurement coverage within
  shared trials. Unmatched case/repetition counts are also reported per comparison.
- `observed_change`: higher, lower, unchanged or unavailable. `preferred_direction`
  describes each metric; it does not declare an overall winner.

Metrics include intent/relevance/style proxies, output validity, unsupported-claim
flags per observed trial, failure/error rates, pipeline latency, benchmark trial
wall time, model calls, revisions and prompt/output token counts. Resource costs
are descriptive tradeoffs, not automatic quality judgments. Optional judging
costs are included in trial wall time, not pipeline calls/latency; see raw results
for separate judge measurements and judgments.

Missing token/style checks stay null, never a made-up zero. Service failures count
in failure/error rates but do not invent a draft's quality measurements. Unsupported
flags are averaged per observed trial rather than compared as unequal raw totals.
Nonfinite numeric measurements are treated as missing so the export is valid JSON.
Duplicate trials and non-completed input are rejected by the comparison builder.

The export contains counters and comparisons, not emails, drafts or prompt text.
It uses deterministic checks rather than evaluator approval as the quality source.
It does not aggregate human judgments or optional independent model judgments.
Mock results measure harness behavior only. Repeated fixed-seed trials and a small
synthetic fixture set do not establish statistical significance or justify a claim
that one system is better overall.

## Code path

`main()` in `src/benchmarks/sample.py` runs the experiment and passes its completed
result to `build_comparison()` in `src/benchmarks/comparison.py`. `metric_value()`
extracts a measured value from a trial; `build_comparison()` groups trials, matches
pairs, and computes the differences. No generation/evaluation logic is changed.
Programmatic callers can use `build_comparison(run_benchmark(config))` explicitly;
`run_benchmark()` itself still returns data without writing final result files.
