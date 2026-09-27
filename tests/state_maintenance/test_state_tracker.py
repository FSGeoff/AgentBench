import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[2] / "src/server/tasks/alfworld/state_tracker.py"
SPEC = importlib.util.spec_from_file_location("state_tracker", MODULE_PATH)
state_tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_tracker)


class StateTrackerTests(unittest.TestCase):
    def test_tracks_success_failure_repetition_and_plan(self):
        tracker = state_tracker.StateTracker("Put the mug on the table.", "You are in a kitchen.")
        successful = tracker.update(
            "go to cabinet 1",
            "Cabinet 1 is open.",
            "THOUGHT: I should find and take the mug next.\nACTION: go to cabinet 1",
        )
        self.assertFalse(successful["action_failed"])
        self.assertIn("go to cabinet 1", tracker.state.completed_steps)
        self.assertEqual(tracker.state.remaining_steps, "I should find and take the mug next.")

        tracker.update("take mug 1", "Nothing happened.", "ACTION: take mug 1")
        repeated_failure = tracker.update("take mug 1", "Nothing happened.", "ACTION: take mug 1")
        self.assertTrue(repeated_failure["repeated_action"])
        self.assertEqual(tracker.repeated_actions, 1)
        self.assertEqual(tracker.repeated_failed_actions, 1)
        self.assertIn("repeated_failed_action", tracker.state_related_errors)

    def test_render_contains_all_proposed_fields(self):
        rendered = state_tracker.StateTracker("Goal", "Observation").render()
        for label in ("Original goal", "Current situation", "Confirmed successful actions", "Failed actions", "Remaining steps"):
            self.assertIn(label, rendered)

    def test_failure_detection_is_case_insensitive(self):
        self.assertTrue(state_tracker.action_failed("NOTHING HAPPENED"))
        self.assertFalse(state_tracker.action_failed("You open the drawer."))


if __name__ == "__main__":
    unittest.main()
