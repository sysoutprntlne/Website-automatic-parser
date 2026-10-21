from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.benchmark_llama32 import ROOT, main


def fake_benchmark(command, **kwargs):
    output = Path(command[command.index("--output") + 1])
    output.mkdir(parents=True)
    result = {
        "status": "completed",
        "run_type": "real-ollama",
        "judged": "--judge" in command,
        "results": [{"error": None}],
    }
    (output / "results.json").write_text(json.dumps(result))
    (output / "comparison.json").write_text(json.dumps({"judged": result["judged"]}))


class BenchmarkScriptTests(unittest.TestCase):
    def test_sequential_commands_named_outputs_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            with (
                patch(
                    "scripts.benchmark_llama32.subprocess.run",
                    side_effect=fake_benchmark,
                ) as runner,
                patch.dict(
                    os.environ,
                    {"REPLY_MODEL": "other", "REPLY_EVALUATOR_MODEL": "other"},
                ),
            ):
                main(["--output", directory])
                first, second = runner.call_args_list
                self.assertNotIn("--judge", first.args[0])
                self.assertIn("--judge", second.args[0])
                for call in (first, second):
                    command = call.args[0]
                    self.assertIn("--real", command)
                    self.assertEqual(command[command.index("--repeats") + 1], "3")
                    self.assertEqual(call.kwargs["env"]["REPLY_MODEL"], "llama3.2")
                    self.assertEqual(
                        call.kwargs["env"]["REPLY_EVALUATOR_MODEL"], "llama3.2"
                    )
                    self.assertEqual(call.kwargs["cwd"], ROOT)
                    self.assertTrue(call.kwargs["check"])
                self.assertEqual(os.environ["REPLY_MODEL"], "other")
                main(["--output", directory])
            batches = list(Path(directory).iterdir())
            self.assertEqual(len(batches), 2)
            for batch in batches:
                standard = json.loads((batch / "llama3.2_results.json").read_text())
                judged = json.loads(
                    (batch / "llama3.2_model_judgment_results.json").read_text()
                )
                self.assertFalse(standard["judged"])
                self.assertTrue(judged["judged"])
                self.assertTrue((batch / "llama3.2_comparison.json").exists())
                self.assertTrue(
                    (batch / "llama3.2_model_judgment_comparison.json").exists()
                )

    def test_failed_first_run_stops_before_judged_run(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            with patch(
                "scripts.benchmark_llama32.subprocess.run",
                side_effect=subprocess.CalledProcessError(2, ["benchmark"]),
            ) as runner:
                with self.assertRaises(SystemExit) as error:
                    main(["--output", directory])
                self.assertEqual(error.exception.code, 2)
                runner.assert_called_once()

    def test_custom_model_tag_safe_names_and_repeats(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            with patch(
                "scripts.benchmark_llama32.subprocess.run", side_effect=fake_benchmark
            ) as runner:
                main(
                    [
                        "--output",
                        directory,
                        "--model",
                        "llama3.2:3b-instruct-q4_K_M",
                        "--evaluator-model",
                        "judge-test",
                        "--repeats",
                        "1",
                        "--quiet",
                    ]
                )
                for call in runner.call_args_list:
                    self.assertEqual(
                        call.kwargs["env"]["REPLY_EVALUATOR_MODEL"], "judge-test"
                    )
                    self.assertIn("--quiet", call.args[0])
                    self.assertEqual(
                        call.args[0][call.args[0].index("--repeats") + 1], "1"
                    )
            batch = next(Path(directory).iterdir())
            self.assertTrue(
                (batch / "llama3.2_3b-instruct-q4_K_M_results.json").exists()
            )

    def test_all_service_errors_keep_results_and_skip_second_run(self):
        def failed_trials(command, **kwargs):
            fake_benchmark(command, **kwargs)
            output = Path(command[command.index("--output") + 1]) / "results.json"
            result = json.loads(output.read_text())
            result["results"] = [{"error": "ConnectionError"}]
            output.write_text(json.dumps(result))

        with (
            tempfile.TemporaryDirectory() as directory,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            with patch(
                "scripts.benchmark_llama32.subprocess.run", side_effect=failed_trials
            ) as runner:
                with self.assertRaises(SystemExit) as error:
                    main(["--output", directory])
                self.assertEqual(error.exception.code, 1)
                runner.assert_called_once()
            batch = next(Path(directory).iterdir())
            self.assertTrue((batch / "llama3.2_results.json").exists())
            self.assertFalse((batch / "llama3.2_model_judgment_results.json").exists())
