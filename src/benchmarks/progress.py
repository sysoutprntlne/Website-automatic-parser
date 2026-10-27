"""Terminal progress and content-free, flushed benchmark metric snapshots."""

import json
import sys
import threading
import time
from pathlib import Path


def percentage(value):
    return "unavailable" if value is None else f"{value:.1%}"


class TrialProgress:
    """Poll counters during a blocking model request; never stream prompt text."""

    def __init__(self, model, emit, details, interval=5.0):
        self.model, self.emit, self.details = model, emit, details
        self.interval = interval
        self.stopped = threading.Event()
        self.worker = None

    def snapshot(self, event):
        self.emit(
            event,
            **self.details,
            trial_elapsed_seconds=time.perf_counter() - self.started,
            metrics=self.model.metrics(),
        )

    def __enter__(self):
        self.started = time.perf_counter()
        self.snapshot("trial_started")
        self.worker = threading.Thread(target=self.poll, daemon=True)
        self.worker.start()
        return self

    def poll(self):
        while not self.stopped.wait(self.interval):
            try:
                self.snapshot("heartbeat")
            except Exception:
                # Surface reporter failures in the owning thread, not silently.
                self.error = sys.exc_info()[1]
                return

    def __exit__(self, *exc):
        self.stopped.set()
        self.worker.join()
        if not exc[0] and hasattr(self, "error"):
            raise self.error


class ProgressOutput:
    """One JSON event per line, latest state as JSON, and concise terminal output."""

    def __init__(self, directory, quiet=False, stream=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.stream = stream if stream is not None else sys.stderr
        self.quiet = quiet
        self.latest = {}

    def __call__(self, event):
        self.latest = event
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as output:
            output.write(json.dumps(event) + "\n")
            output.flush()
        temporary = self.directory / "progress.json.tmp"
        temporary.write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.directory / "progress.json")
        if self.quiet:
            return
        kind = event["event"]
        prefix = f"[{event['completed']}/{event['total']}]"
        if kind == "run_started":
            print(
                f"{prefix} {event['run_type']} | generator={event['model']} | "
                f"evaluator={event['evaluator_model']}\n"
                "Quality values are deterministic proxies; model approval is separate.",
                file=self.stream,
                flush=True,
            )
        elif kind in ("trial_started", "heartbeat"):
            metrics = event["metrics"]
            tokens = metrics.get("output_tokens")
            print(
                f"{prefix} repeat={event['repeat']} {event['case']} / {event['mode']} "
                f"{kind} | {event['trial_elapsed_seconds']:.1f}s | "
                f"calls={metrics.get('model_calls', 0)} | "
                f"output_tokens={tokens if tokens is not None else 'unavailable'}",
                file=self.stream,
                flush=True,
            )
        elif kind == "trial_finished":
            print(
                f"{prefix} {event['case']} / {event['mode']} "
                f"{'FAIL' if event['failed'] else 'PASS'} (proxy checks) | "
                f"trial={event['trial_wall_seconds']:.2f}s | "
                f"calls={event['metrics'].get('model_calls', 0)} | "
                f"revisions={event['metrics'].get('revisions', 'unavailable')} | "
                f"prompt_tokens={event['metrics'].get('prompt_tokens')} | "
                f"output_tokens={event['metrics'].get('output_tokens')} | "
                f"error={event['error'] or 'none'}",
                file=self.stream,
                flush=True,
            )
            for mode, summary in event["summary"].items():
                if not summary["completed_trials"]:
                    continue
                mean = summary["latency_seconds"]
                latency = f"{mean:.2f}s" if mean is not None else "unavailable"
                print(
                    f"  {mode}: n={summary['completed_trials']} | mean={latency} | "
                    f"intent={percentage(summary['intent_preservation_proxy'])} | "
                    f"relevance={percentage(summary['relevance_completeness_proxy'])} | "
                    f"style={percentage(summary['style_fit_proxy'])} | "
                    f"unsupported_flags={summary['unsupported_claims_proxy_count']} | "
                    f"failure_rate={summary['failure_rate']:.1%} | "
                    f"errors={summary['error_count']} | "
                    f"mean_calls={summary['model_calls']} | mean_revisions={summary['revisions']}",
                    file=self.stream,
                    flush=True,
                )
        else:
            print(
                f"{prefix} {kind} | elapsed={event['elapsed_seconds']:.1f}s",
                file=self.stream,
                flush=True,
            )

    def stopped(self, status):
        if self.latest:
            self(dict(self.latest, event=status))
