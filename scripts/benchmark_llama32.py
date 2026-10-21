"""Run real benchmarks, then repeat with model judging, keeping both JSON outputs."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run_once(batch, prefix, judged, repeats, environment, quiet=False):
    label = "model_judgment" if judged else "standard"
    output = batch / label
    command = [
        sys.executable,
        "-m",
        "src.benchmarks.sample",
        "--real",
        "--repeats",
        str(repeats),
        "--output",
        str(output),
    ]
    if judged:
        command.append("--judge")
    if quiet:
        command.append("--quiet")
    print(f"Starting {label} benchmark: {output}", flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)

    result = json.loads((output / "results.json").read_text(encoding="utf-8"))
    if result.get("status") != "completed" or result.get("run_type") != "real-ollama":
        raise RuntimeError(f"Expected completed real benchmark results in {output}")
    name = f"{prefix}_model_judgment" if judged else prefix
    for source, suffix in (
        ("results.json", "results"),
        ("comparison.json", "comparison"),
    ):
        destination = batch / f"{name}_{suffix}.json"
        shutil.copyfile(output / source, destination)
        print(f"Saved: {destination}", flush=True)
    trials = result.get("results", [])
    if not trials or all(trial.get("error") for trial in trials):
        raise RuntimeError(
            f"No trial completed without service errors. Inspect {output}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument(
        "--evaluator-model",
        help="Feedback evaluator and independent judge model (defaults to --model)",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "benchmark-results")
    parser.add_argument("--quiet", action="store_true", help="Hide live progress lines")
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= 20:
        parser.error("repeats must be 1..20")
    if not args.model.strip() or (
        args.evaluator_model is not None and not args.evaluator_model.strip()
    ):
        parser.error("Model names must not be empty")

    environment = dict(os.environ)
    environment["REPLY_MODEL"] = args.model
    environment["REPLY_EVALUATOR_MODEL"] = args.evaluator_model or args.model
    prefix = re.sub(r"[^A-Za-z0-9._-]", "_", args.model)
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch = Path(tempfile.mkdtemp(prefix=f"{prefix}_{timestamp}_", dir=output))
    print(f"Batch directory: {batch}", flush=True)
    print(
        f"Generator: {args.model}; evaluator/judge: {environment['REPLY_EVALUATOR_MODEL']}",
        flush=True,
    )
    try:
        run_once(batch, prefix, False, args.repeats, environment, args.quiet)
        run_once(batch, prefix, True, args.repeats, environment, args.quiet)
    except KeyboardInterrupt:
        print(f"Interrupted. Completed outputs remain in {batch}", file=sys.stderr)
        raise SystemExit(130) from None
    except subprocess.CalledProcessError as error:
        print(
            f"Benchmark exited with code {error.returncode}. Outputs: {batch}",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode if error.returncode > 0 else 1) from None
    except (OSError, ValueError, RuntimeError) as error:
        print(f"{error}. Retained outputs: {batch}", file=sys.stderr)
        raise SystemExit(1) from None
    print(f"Both benchmarks completed. JSON files: {batch}", flush=True)


if __name__ == "__main__":
    main()
