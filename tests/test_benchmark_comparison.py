import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.benchmarks.comparison import build_comparison
from src.benchmarks.sample import main


def trial(mode, case, latency, intent=True):
    return {
        "mode": mode,
        "case": case,
        "repeat": 0,
        "metrics": {
            "latency_seconds": latency,
            "model_calls": 2,
            "output_tokens": None,
        },
        "deterministic": {
            "intent_preservation_proxy": intent,
            "relevance_completeness_proxy": True,
            "style_fit_proxy": None,
            "output_valid": True,
            "unsupported_claims_proxy": [],
        },
        "failed": not intent,
        "error": None,
        "draft": {"body": "PRIVATE SYNTHETIC CONTENT"},
    }


def completed_data():
    return {
        "status": "completed",
        "run_id": "synthetic-test-run",
        "run_type": "mock-harness-only",
        "timestamp_utc": "2026-10-21T00:00:00+00:00",
        "fixture_sha256": "synthetic-fixture-hash",
        "config": {"model": "synthetic", "evaluator_model": "synthetic", "seed": 42},
        "repeats": 1,
        "results": [
            trial("baseline", "a", 10, intent=False),
            trial("baseline", "b", 100),
            trial("rag", "a", 5),
            trial("rag", "b", None),
            trial("rag_feedback", "a", 8),
            trial("rag_feedback", "b", 9),
        ],
    }


class BenchmarkComparisonTests(unittest.TestCase):
    def test_paired_deltas_percentages_and_coverage(self):
        comparison = build_comparison(completed_data())
        self.assertEqual(len(comparison["comparisons"]), 3)
        rag = comparison["comparisons"][0]
        self.assertEqual((rag["reference"], rag["candidate"]), ("baseline", "rag"))
        latency = rag["metrics"]["latency_seconds"]
        # Baseline's second latency is excluded from the paired difference.
        self.assertEqual(latency["reference_mean"], 10)
        self.assertEqual(latency["candidate_mean"], 5)
        self.assertEqual(latency["delta"], -5)
        self.assertEqual(latency["percent_change"], -50)
        self.assertEqual(latency["paired_observations"], 1)
        self.assertEqual(latency["missing_metric_pairs"], 1)
        self.assertEqual(latency["observed_change"], "lower")
        intent = rag["metrics"]["intent_preservation_proxy"]
        self.assertEqual(intent["delta"], 0.5)
        self.assertEqual(intent["percentage_point_change"], 50)
        self.assertEqual(intent["percent_change"], 100)
        self.assertIsNone(rag["metrics"]["style_fit_proxy"]["delta"])
        self.assertEqual(
            rag["metrics"]["style_fit_proxy"]["observed_change"], "unavailable"
        )
        self.assertEqual(
            comparison["interpretation"]["statistical_significance"], "not_tested"
        )
        self.assertNotIn("PRIVATE SYNTHETIC CONTENT", json.dumps(comparison))

    def test_zero_reference_and_failed_trials_are_not_invented_measurements(self):
        data = completed_data()
        for row in data["results"]:
            row["metrics"]["model_calls"] = 0
        failed = data["results"][0]
        failed.update(error="RuntimeError", failed=True, deterministic=None)
        data["results"][1]["metrics"]["latency_seconds"] = float("nan")
        comparison = build_comparison(data)
        baseline = comparison["configurations"]["baseline"]["metrics"]
        self.assertEqual(baseline["error_rate"]["mean"], 0.5)
        self.assertEqual(baseline["unsupported_claims_per_trial"]["observations"], 1)
        self.assertEqual(baseline["latency_seconds"]["missing"], 1)
        calls = comparison["comparisons"][0]["metrics"]["model_calls"]
        self.assertEqual(calls["delta"], 0)
        self.assertIsNone(calls["percent_change"])
        self.assertIsNone(
            comparison["comparisons"][0]["metrics"]["output_tokens"]["delta"]
        )
        json.dumps(comparison, allow_nan=False)

    def test_unmatched_trials_duplicate_trials_and_incomplete_runs(self):
        data = completed_data()
        data["results"] = [
            row
            for row in data["results"]
            if not (row["mode"] == "rag" and row["case"] == "b")
        ]
        pair = build_comparison(data)["comparisons"][0]
        self.assertEqual(pair["matched_trials"], 1)
        self.assertEqual(pair["unmatched_reference_trials"], 1)
        data["results"].append(copy.deepcopy(data["results"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_comparison(data)
        data["status"] = "interrupted"
        with self.assertRaisesRegex(ValueError, "completed"):
            build_comparison(data)

    def test_cli_creates_comparison_after_mock_run(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with (
                patch("sys.argv", ["benchmark", "--quiet", "--output", directory]),
                redirect_stdout(output),
            ):
                main()
            root = Path(directory)
            result = json.loads((root / "results.json").read_text())
            comparison = json.loads((root / "comparison.json").read_text())
            self.assertEqual(comparison["run_id"], result["run_id"])
            self.assertEqual(comparison["fixture_sha256"], result["fixture_sha256"])
            self.assertEqual(comparison["run_type"], "mock-harness-only")
            self.assertEqual(comparison["status"], "completed")
            self.assertEqual(comparison["configurations"]["baseline"]["trials"], 6)
            self.assertTrue((root / "report.md").exists())
            self.assertFalse((root / "comparison.json.tmp").exists())
            self.assertIn(str(root / "comparison.json"), output.getvalue())
