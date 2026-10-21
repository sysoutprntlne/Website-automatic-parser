# Live benchmark feedback

Run the existing benchmark normally. Live terminal output is on by default:

```bash
.venv/bin/python -m src.benchmarks.sample --real --repeats 1 --output benchmark-results/quick
```

For a credential-free check, omit `--real`. The default heartbeat interval is five
seconds; use `--progress-interval 2` to change it. `--quiet` suppresses live terminal
lines while retaining the final report and progress files. Progress uses stderr;
the final comparison report uses stdout. No dashboard or additional dependencies
are needed.

During a trial, the heartbeat shows the case/configuration, elapsed time,
model-call count, and output-token count where available. The Ollama adapter uses
blocking structured responses, so token counters update when each response returns,
not token by token. A moving elapsed timer means the runner is alive, not that the
model has generated new text. Optional independent judge calls are recorded
separately in `judge_metrics`; the live model counters describe the pipeline.

At the end of each trial it reports calls, revisions, tokens, a trial wall time,
proxy pass/fail, and any service exception type. Running per-configuration summaries
show mean pipeline latency, intent/relevance/style proxies, unsupported-claim flags,
failure rate, service-error count, calls, and revisions. Quality and model approval
are separate: a pipeline evaluator pass does not override independent proxy failures.
Missing token/style information remains unavailable instead of becoming zero.
Trial wall time includes preparation and optional judging; pipeline latency is
measured by Assistant.run and excludes benchmark setup and optional judging.
Failed requests do not necessarily have a completed pipeline latency.

The output directory receives two files immediately:

- `events.jsonl`: flushed, append-only events across runs, identified by `run_id`.
  Contains trial identifiers, counters, aggregate metrics, and deterministic check
  results, without email bodies, drafts, prompts, evaluator feedback, or raw service
  exception messages.
- `progress.json`: atomically replaced snapshot of the latest event, including
  current completed/total counts and running summaries. It can be read by another
  terminal while the run is active.

On Ctrl+C, completed metrics remain in those files and the latest event is marked
`interrupted`; the CLI exits with code 130. There is no automatic resume. Final
`results.json` and `report.md` are still written only after the experiment finishes;
results include the matching run ID. Use separate output directories for experiments
and concurrent runs. If reusing a directory, an old final report may remain during
a new or interrupted run: check the progress status/run ID before treating it as
new results. Synthetic final results include generated draft text as before.

The runner exposes an optional `on_progress(event)` callback for programmatic use.
A background polling thread emits heartbeat callbacks; start/finish callbacks run
on the calling thread. Callback delivery is serialized. Existing callers with no
callback retain their ordinary return value and do not start a reporting thread.

## Choosing a model

Keep both models rather than permanently replacing one before measuring them.
Use the smaller 1B model for iteration, and retain a 3B model as a reference for
quality/latency comparisons. Set BOTH REPLY_MODEL and REPLY_EVALUATOR_MODEL for each
run; otherwise the larger evaluator may remain the bottleneck.

For an initial practical comparison, run each model with the laptop plugged in,
the same OS power profile, shared prompts/settings/attempt limit, and no competing
model workload. Record the model tag, power mode and whether it was a cold or warmed
run. This harness records model/configuration information but does not capture
battery state, temperature, GPU/CPU utilization, or power profiles automatically.
The first request can include model loading; mode shuffling alone does not eliminate
that effect. Warm both models consistently before comparisons of steady-state
latency, or deliberately measure cold-start latency separately. Keep longer runs
comparable in temperature and background activity too.

Use `ollama ps` during inference to inspect CPU/GPU placement. This application's
adapter currently explicitly requests a 16384-token context; changing Ollama's
server-wide default context alone will not override that request. No context,
generation settings, evaluator model, or laptop power settings are changed by the
live reporting feature.

A six-case test with a few repetitions is useful for debugging and spotting tradeoffs,
but it is not sufficient to establish statistical significance. Repeated fixed-seed
runs mostly characterize runtime variability, not independent quality observations.
Use more held-out cases and human review before claiming a quality improvement.
If the smaller model meets the needed quality and latency, use it as the everyday
default; retain the larger model for optional comparison rather than requiring it.
