import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from src.benchmarks.progress import ProgressOutput, TrialProgress
from src.benchmarks.sample import FIXTURES, main, run_benchmark
from src.config import Config


class BenchmarkProgressTests(unittest.TestCase):
    def test_heartbeat_during_blocking_work_and_clean_shutdown(self):
        heartbeat = threading.Event()
        events = []
        model = Mock()
        model.metrics.return_value = {"model_calls": 1, "output_tokens": None}

        def emit(event, **details):
            events.append(dict(event=event, **details))
            if event == "heartbeat":
                heartbeat.set()

        with TrialProgress(
            model, emit, {"case": "synthetic"}, interval=0.01
        ) as tracker:
            self.assertTrue(heartbeat.wait(timeout=2))
        self.assertFalse(tracker.worker.is_alive())
        self.assertEqual(events[0]["event"], "trial_started")
        self.assertEqual(events[-1]["metrics"]["model_calls"], 1)
        self.assertGreaterEqual(events[-1]["trial_elapsed_seconds"], 0)

    def test_failed_calls_report_errors_and_count_completed_trials(self):
        fixtures = json.loads(FIXTURES.read_text())
        fixtures["cases"] = fixtures["cases"][:1]
        events = []
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixtures.json"
            fixture.write_text(json.dumps(fixtures))
            with patch(
                "src.benchmarks.sample.Assistant.run",
                side_effect=RuntimeError("PRIVATE PAYLOAD"),
            ):
                result = run_benchmark(
                    Config(), fixture_path=fixture, on_progress=events.append
                )
        for mode in result["summary"].values():
            self.assertEqual(mode["failure_rate"], 1)
            self.assertEqual(mode["error_count"], 1)
        completed = [event for event in events if event["event"] == "trial_finished"]
        self.assertEqual(len(completed), 3)
        self.assertTrue(all(event["error"] == "RuntimeError" for event in completed))
        self.assertNotIn("PRIVATE PAYLOAD", json.dumps(events))

    def test_cli_writes_flushed_progress_and_preserves_interrupted_status(self):
        fixtures = json.loads(FIXTURES.read_text())
        fixtures["cases"] = fixtures["cases"][:1]
        with tempfile.TemporaryDirectory() as directory:
            stream = io.StringIO()
            output = ProgressOutput(directory, stream=stream)
            fixture = Path(directory) / "fixtures.json"
            fixture.write_text(json.dumps(fixtures))
            result = run_benchmark(Config(), fixture_path=fixture, on_progress=output)
            events = [
                json.loads(line)
                for line in (Path(directory) / "events.jsonl").read_text().splitlines()
            ]
            latest = json.loads((Path(directory) / "progress.json").read_text())
            self.assertEqual(latest["summary"], result["summary"])
            self.assertEqual(events[-1]["event"], "run_finished")
            self.assertIn("proxy checks", stream.getvalue())
            self.assertIn("failure_rate", stream.getvalue())
            output.stopped("interrupted")
            self.assertEqual(
                json.loads((Path(directory) / "progress.json").read_text())["event"],
                "interrupted",
            )
            self.assertFalse((Path(directory) / "progress.json.tmp").exists())

    def test_cli_interrupt_exits_with_130_and_keeps_progress(self):
        with tempfile.TemporaryDirectory() as directory:

            def interrupt(*args, **kwargs):
                kwargs["on_progress"](
                    {
                        "event": "run_started",
                        "completed": 0,
                        "total": 18,
                        "elapsed_seconds": 0,
                    }
                )
                raise KeyboardInterrupt()

            with (
                patch("sys.argv", ["benchmark", "--quiet", "--output", directory]),
                patch("src.benchmarks.sample.run_benchmark", side_effect=interrupt),
            ):
                with self.assertRaises(SystemExit) as caught:
                    main()
            self.assertEqual(caught.exception.code, 130)
            latest = json.loads((Path(directory) / "progress.json").read_text())
            self.assertEqual(latest["event"], "interrupted")
            self.assertFalse((Path(directory) / "results.json").exists())
            self.assertFalse((Path(directory) / "comparison.json").exists())
