# Run Llama 3.2 benchmarks sequentially

From the repository root:

```bash
.venv/bin/python scripts/benchmark_llama32.py
```

The script invokes the existing real benchmark twice, sequentially, with three
repetitions per run:

1. `--real`: baseline, RAG, and RAG with feedback; no independent benchmark judge.
2. `--real --judge`: the same configurations, with independent model assessment
   of each generated reply in addition to the pipeline's existing evaluator.

The second command regenerates drafts; it does not just score the first run's
saved replies. Each run therefore has its own run ID and measurements. The script
uses the same generation/evaluation models, fixtures, shared settings and repeat
count in both commands. Independent judging introduces additional cost and may
affect system load between trials; compare pipeline latency and judge costs with
that limitation in mind. This is not a new generation configuration or a proof of
statistical significance.

Outputs have a fresh UTC timestamp and unique suffix each time. Defaults:

```text
benchmark-results/llama3.2_1b-instruct-q4_K_M_<UTC timestamp>_<unique suffix>/
    llama3.2_1b-instruct-q4_K_M_results.json
    llama3.2_1b-instruct-q4_K_M_comparison.json
    llama3.2_1b-instruct-q4_K_M_model_judgment_results.json
    llama3.2_1b-instruct-q4_K_M_model_judgment_comparison.json
    standard/
        results.json
        comparison.json
        report.md
        progress.json
        events.jsonl
    model_judgment/
        results.json
        comparison.json
        report.md
        progress.json
        events.jsonl
```

The four named JSON files are copies of each run's original outputs; progress and
readable reports remain in the corresponding subdirectory. Existing batches are
never overwritten. Live progress stays enabled by default. The terminal prints
both the batch directory and each named JSON file as it is saved.

```bash
# Shorter first test: one repetition per run
.venv/bin/python scripts/benchmark_llama32.py --repeats 1
# Explicit model tag, optional separate evaluator/benchmark judge
.venv/bin/python scripts/benchmark_llama32.py \
  --model llama3.2:3b-instruct-q4_K_M \
  --evaluator-model llama3.2:3b-instruct-q4_K_M \
  --output benchmark-results
```

Default generator and evaluator/judge are both `llama3.2:1b-instruct-q4_K_M`. The script explicitly
sets REPLY_MODEL and REPLY_EVALUATOR_MODEL in its child processes, so an older
export selecting another model cannot silently change these runs. `--model`
changes the generator and default evaluator together; `--evaluator-model` overrides
both the pipeline feedback evaluator and independent benchmark judge. Model tags
are sanitized only for filenames (for example, `:` becomes `_`), while the actual
Ollama model tag is preserved. Other exported REPLY settings are inherited; .env
files are not loaded automatically. Your shell/configuration files are not changed.

Ollama must be running and the selected models installed. This script does not
start Ollama or download models. It does not access Gmail: real model calls use
the existing synthetic benchmark fixtures and temporary Chroma memory.

If the first command exits unsuccessfully or all its trials have service errors,
the judged run does not start. Completed output remains available for inspection.
Proxy quality failures alone do not stop the second run. Ctrl+C stops the batch,
retaining already completed files and progress. Rerunning starts a fresh batch;
there is no automatic resume. `--quiet` hides live progress lines if desired.
