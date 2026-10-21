import json
import tempfile
import unittest
from pathlib import Path
from src.benchmarks.sample import FIXTURES, run_benchmark, report
from src.config import Config


class BenchmarkTests(unittest.TestCase):
    def test_modes_and_metrics(self):
        events = []
        data = run_benchmark(Config(), on_progress=events.append)
        self.assertEqual(data["run_type"], "mock-harness-only")
        self.assertEqual(len(data["results"]), 18)
        for row in data["results"]:
            self.assertIsNone(row["error"])
            self.assertIsNone(row["human_review"])
            self.assertIsNone(row["model_judgment"])
            if row["mode"] != "rag_feedback":
                self.assertEqual(row["metrics"]["model_calls"], 2)
                self.assertIsNone(row["pipeline_evaluator_approval"])
            if row["mode"] == "baseline" or row["case"] == "empty-memory":
                self.assertEqual(row["metrics"]["retrieved_examples"], 0)
            elif row["mode"].startswith("rag"):
                self.assertGreater(row["metrics"]["retrieved_examples"], 0)
        self.assertIn("mock-harness-only", report(data))
        self.assertEqual(events[0]["event"], "run_started")
        self.assertEqual(events[0]["completed"], 0)
        self.assertEqual(events[-1]["event"], "run_finished")
        self.assertEqual(events[-1]["completed"], 18)
        self.assertEqual(events[-1]["summary"], data["summary"])
        completed = [event for event in events if event["event"] == "trial_finished"]
        self.assertEqual(
            [event["completed"] for event in completed], list(range(1, 19))
        )
        for event in completed:
            self.assertNotIn("draft", event)
            self.assertNotIn("body", json.dumps(event))
        self.assertEqual(len({event["run_id"] for event in events}), 1)

    def test_reject_leaked_target(self):
        fixtures = json.loads(FIXTURES.read_text())
        fixtures["style_examples"][0]["body"] = fixtures["cases"][0]["target_reply"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixtures.json"
            path.write_text(json.dumps(fixtures))
            with self.assertRaises(ValueError):
                run_benchmark(Config(), fixture_path=path)
