import unittest

from src.server.tasks.alfworld.utils import normalize_agent_turn


class TurnNormalizationTests(unittest.TestCase):
    def test_preserves_single_action(self):
        self.assertEqual(
            normalize_agent_turn("ACTION: go to desk 1"),
            "ACTION: go to desk 1",
        )

    def test_preserves_thought_and_first_action(self):
        output = (
            "THOUGHT: I should inspect the desk.\n"
            "ACTION: go to desk 1\n"
            "USER: On the desk, you see a pencil.\n"
            "ACTION: take pencil 1 from desk 1"
        )

        self.assertEqual(
            normalize_agent_turn(output),
            "THOUGHT: I should inspect the desk.\n"
            "ACTION: go to desk 1",
        )

    def test_removes_same_line_simulated_continuation(self):
        output = (
            "ACTION: look USER: You see a shelf. "
            "ACTION: go to shelf 1"
        )

        self.assertEqual(
            normalize_agent_turn(output),
            "ACTION: look",
        )

    def test_leaves_missing_action_for_existing_validator(self):
        output = "THOUGHT: I am unsure what to do."
        self.assertEqual(normalize_agent_turn(output), output)


if __name__ == "__main__":
    unittest.main()
