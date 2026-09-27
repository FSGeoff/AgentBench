"""Observable-only task-state tracking for the ALFWorld experiment.

The tracker deliberately uses only the goal, model output, chosen action, and
environment observation.  It never reads privileged ALFWorld simulator state.
"""

from dataclasses import asdict, dataclass, field
import re
from typing import Dict, List, Optional


FAILURE_MARKERS = (
    "nothing happened",
    "nothing happens",
    "can't",
    "cannot",
    "not possible",
    "invalid action",
)


def extract_thought(model_output: str) -> Optional[str]:
    """Return the model's latest THOUGHT text without changing its action."""
    match = re.search(r"THOUGHT:\s*(.*?)(?=\n\s*ACTION:|$)", model_output, re.I | re.S)
    if not match:
        return None
    thought = " ".join(match.group(1).strip().split())
    return thought or None


def action_failed(observation: str) -> bool:
    normalized = observation.lower()
    return any(marker in normalized for marker in FAILURE_MARKERS)


@dataclass
class StructuredTaskState:
    original_goal: str
    current_observation: str
    completed_steps: List[str] = field(default_factory=list)
    failed_actions: List[str] = field(default_factory=list)
    remaining_steps: str = "Infer the next required steps from the goal and current observation."

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class StateTracker:
    """Maintain a compact, auditable summary of an ALFWorld trajectory."""

    def __init__(self, original_goal: str, initial_observation: str):
        self.state = StructuredTaskState(
            original_goal=" ".join(original_goal.split()),
            current_observation=" ".join(initial_observation.split()),
        )
        self.action_counts: Dict[str, int] = {}
        self.failed_action_counts: Dict[str, int] = {}
        self.repeated_actions = 0
        self.repeated_failed_actions = 0
        self.state_related_errors: List[str] = []

    def update(self, action: str, observation: str, model_output: str = "") -> Dict[str, object]:
        action = " ".join(action.strip().lower().split())
        failed = action_failed(observation)

        previous_count = self.action_counts.get(action, 0)
        repeated = previous_count > 0
        self.action_counts[action] = previous_count + 1
        if repeated:
            self.repeated_actions += 1
            self._record_error("repeated_action")

        if failed:
            self.state.failed_actions.append(action)
            prior_failures = self.failed_action_counts.get(action, 0)
            self.failed_action_counts[action] = prior_failures + 1
            if prior_failures > 0:
                self.repeated_failed_actions += 1
                self._record_error("repeated_failed_action")
        else:
            self.state.completed_steps.append(action)

        thought = extract_thought(model_output)
        if thought:
            self.state.remaining_steps = thought
        self.state.current_observation = " ".join(observation.split())

        return {
            "action_failed": failed,
            "repeated_action": repeated,
            "state": self.snapshot(),
        }

    def _record_error(self, label: str) -> None:
        if label not in self.state_related_errors:
            self.state_related_errors.append(label)

    def snapshot(self) -> Dict[str, object]:
        return self.state.to_dict()

    def render(self) -> str:
        completed = "; ".join(self.state.completed_steps) or "None confirmed"
        failed = "; ".join(self.state.failed_actions) or "None"
        return (
            "\nSTRUCTURED TASK STATE (use this summary; verify it against the latest observation):\n"
            f"- Original goal: {self.state.original_goal}\n"
            f"- Current situation: {self.state.current_observation}\n"
            f"- Confirmed successful actions: {completed}\n"
            f"- Failed actions: {failed}\n"
            f"- Remaining steps / current plan: {self.state.remaining_steps}\n"
        )

