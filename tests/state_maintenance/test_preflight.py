import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[2] / "research/state_maintenance/preflight.py"
SPEC = importlib.util.spec_from_file_location("preflight", MODULE_PATH)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def test_repository_experiment_configuration(self):
        report = preflight.run_checks()
        self.assertEqual(report["pilot_tasks"], 4)
        self.assertEqual(report["full_tasks"], 24)
        self.assertEqual(report["conditions"], 2)

    def test_rejects_mismatched_pair(self):
        definitions = {
            "base": {"parameters": {"split": "same", "state_mode": "baseline"}},
            "state": {"parameters": {"split": "different", "state_mode": "structured"}},
        }
        with self.assertRaises(ValueError):
            preflight.check_pair(definitions, "base", "state", "same")


if __name__ == "__main__":
    unittest.main()
