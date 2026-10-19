import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).parents[2] / "src/server/tasks/alfworld/state_tracker.py"
SPEC = importlib.util.spec_from_file_location("state_tracker", MODULE_PATH)
state_tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_tracker)


class StateTrackerTests(unittest.TestCase):
    def test_replaces_current_facts_and_marks_superseded(self):
        tracker = state_tracker.StateTracker("Put the mug on the table.", "You are in a kitchen.")
        tracker.update("go to cabinet 1", "You arrive at cabinet 1.")
        tracker.update("go to sinkbasin 1", "You arrive at sinkbasin 1.")
        self.assertEqual(tracker.state.current_location, "sinkbasin 1")
        self.assertTrue(any(item["kind"] == "location" for item in tracker.state.superseded_facts))
        self.assertNotIn("cabinet 1", tracker.render().split("Latest observation")[0])

    def test_context_failure_expires_after_state_change(self):
        tracker = state_tracker.StateTracker("Put the mug on the table.", "Kitchen.")
        tracker.update("take mug 1 from cabinet 1", "Nothing happened.")
        self.assertTrue(tracker.state.contextual_failures)
        tracker.update("go to cabinet 1", "You arrive at cabinet 1.")
        self.assertFalse(tracker.state.contextual_failures)

    def test_goal_reminder_and_structured_record_share_goal(self):
        tracker = state_tracker.StateTracker("Put the mug on the table.", "Kitchen.")
        self.assertIn("Put the mug on the table.", tracker.render_goal_reminder())
        self.assertIn("CURRENT OBSERVABLE STATE", tracker.render())
        self.assertNotIn("Remaining steps", tracker.render())

    def test_flags_state_inconsistent_post_change_decision(self):
        tracker = state_tracker.StateTracker("Put the mug on the table.", "Kitchen.")
        tracker.update("take mug 1 from cabinet 1", "You take mug 1.")
        decision = tracker.evaluate_decision("take mug 1 from cabinet 1")
        self.assertTrue(decision["eligible"])
        self.assertFalse(decision["state_consistent"])
        self.assertIn("take_object_already_held", decision["reasons"])
        self.assertEqual(tracker.state_inconsistent_actions, 1)

    def test_failure_detection_is_case_insensitive(self):
        self.assertTrue(state_tracker.action_failed("NOTHING HAPPENED"))
        self.assertFalse(state_tracker.action_failed("You open the drawer."))


if __name__ == "__main__":
    unittest.main()
