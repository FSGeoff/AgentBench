import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[2] / "research/state_maintenance/analyze_results.py"
SPEC = importlib.util.spec_from_file_location("analyze_results", MODULE_PATH)
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def record(index, success, status, rounds, repeats):
    return {
        "index": index,
        "output": {
            "status": status,
            "result": {
                "result": success,
                "experiment": {
                    "interaction_rounds": rounds,
                    "repeated_actions": repeats,
                    "repeated_failed_actions": 0,
                    "failure_types": [],
                    "state_related_errors": [],
                },
            },
        },
    }


class AnalysisTests(unittest.TestCase):
    def test_summary_and_paired_comparison(self):
        baseline = [analysis.normalize_record(record(0, 0, "task limit reached", 35, 2)), analysis.normalize_record(record(1, 1, "completed", 8, 0))]
        structured = [analysis.normalize_record(record(0, 1, "completed", 12, 0)), analysis.normalize_record(record(1, 1, "completed", 7, 0))]
        summary = analysis.summarize(baseline)
        self.assertEqual(summary["completion_rate"], 0.5)
        self.assertEqual(summary["task_limit_exceeded"], 1)
        paired = analysis.paired_comparison(baseline, structured)
        self.assertEqual(paired, {"matched_tasks": 2, "improved": 1, "regressed": 0, "unchanged": 1})

    def test_loads_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(json.dumps(record(3, 1, "completed", 4, 0)) + "\n", encoding="utf-8")
            rows = analysis.load_runs(path)
        self.assertEqual(rows[0]["index"], 3)
        self.assertTrue(rows[0]["success"])


if __name__ == "__main__":
    unittest.main()
