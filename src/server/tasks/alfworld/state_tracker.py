"""Observable-only current-state tracking for the ALFWorld experiment.

The tracker uses only the task text, selected actions, and visible ALFWorld
observations. It never reads simulator state or an expert plan.
"""

from dataclasses import asdict, dataclass, field
import re
from typing import Dict, List


FAILURE_MARKERS = (
    "nothing happened",
    "nothing happens",
    "can't",
    "cannot",
    "not possible",
    "invalid action",
)


def normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def action_failed(observation: str) -> bool:
    normalized = normalize(observation)
    return any(marker in normalized for marker in FAILURE_MARKERS)


@dataclass
class StructuredTaskState:
    original_goal: str
    current_observation: str
    current_location: str = "Not yet confirmed"
    inventory: List[str] = field(default_factory=list)
    object_conditions: Dict[str, str] = field(default_factory=dict)
    container_states: Dict[str, str] = field(default_factory=dict)
    confirmed_progress: List[str] = field(default_factory=list)
    contextual_failures: List[Dict[str, str]] = field(default_factory=list)
    superseded_facts: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class StateTracker:
    """Maintain one current value per observable state field."""

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
        self.pending_decision_point = False
        self.decision_points = 0
        self.state_consistent_decisions = 0
        self.state_inconsistent_actions = 0

    def _context_signature(self) -> str:
        return repr((
            self.state.current_location,
            tuple(sorted(self.state.inventory)),
            tuple(sorted(self.state.container_states.items())),
        ))

    def _replace_mapping_fact(self, kind: str, key: str, value: str, mapping: Dict[str, str]) -> bool:
        old = mapping.get(key)
        if old == value:
            return False
        if old is not None:
            self.state.superseded_facts.append(
                {"kind": kind, "entity": key, "old": old, "new": value}
            )
        mapping[key] = value
        return True

    def _record_progress(self, action: str) -> None:
        if action not in self.state.confirmed_progress:
            self.state.confirmed_progress.append(action)

    def _apply_success(self, action: str) -> bool:
        changed = False

        match = re.match(r"go to (.+)", action)
        if match:
            location = match.group(1)
            if self.state.current_location != location:
                if self.state.current_location != "Not yet confirmed":
                    self.state.superseded_facts.append(
                        {
                            "kind": "location",
                            "entity": "agent",
                            "old": self.state.current_location,
                            "new": location,
                        }
                    )
                self.state.current_location = location
                changed = True

        match = re.match(r"take (.+?)(?: from .+)?$", action)
        if match:
            obj = match.group(1)
            if obj not in self.state.inventory:
                self.state.inventory.append(obj)
                changed = True

        match = re.match(r"put (.+?) (?:in|on) .+$", action)
        if match:
            obj = match.group(1)
            if obj in self.state.inventory:
                self.state.inventory.remove(obj)
                changed = True

        match = re.match(r"(clean|heat|cool) (.+?)(?: with .+)?$", action)
        if match:
            condition, obj = match.groups()
            changed = self._replace_mapping_fact(
                "object_condition", obj, condition, self.state.object_conditions
            ) or changed

        match = re.match(r"(open|close) (.+)$", action)
        if match:
            verb, container = match.groups()
            changed = self._replace_mapping_fact(
                "container_state",
                container,
                "open" if verb == "open" else "closed",
                self.state.container_states,
            ) or changed

        self._record_progress(action)
        return changed

    def evaluate_decision(self, action: str) -> Dict[str, object]:
        """Flag obvious contradictions at a predefined post-change decision point."""
        action = normalize(action)
        eligible = self.pending_decision_point
        reasons: List[str] = []

        match = re.match(r"take (.+?)(?: from .+)?$", action)
        if match and match.group(1) in self.state.inventory:
            reasons.append("take_object_already_held")

        match = re.match(r"go to (.+)", action)
        if match and match.group(1) == self.state.current_location:
            reasons.append("go_to_current_location")

        match = re.match(r"(open|close) (.+)$", action)
        if match:
            verb, container = match.groups()
            desired = "open" if verb == "open" else "closed"
            if self.state.container_states.get(container) == desired:
                reasons.append("repeat_confirmed_container_state")

        match = re.match(r"(clean|heat|cool) (.+?)(?: with .+)?$", action)
        if match:
            condition, obj = match.groups()
            if self.state.object_conditions.get(obj) == condition:
                reasons.append("repeat_confirmed_object_condition")

        match = re.match(r"put (.+?) (?:in|on) .+$", action)
        if match and match.group(1) not in self.state.inventory:
            reasons.append("put_object_not_held")

        consistent = not reasons
        if eligible:
            self.decision_points += 1
            if consistent:
                self.state_consistent_decisions += 1
            else:
                self.state_inconsistent_actions += 1
                self._record_error("state_inconsistent_action")
        self.pending_decision_point = False
        return {"eligible": eligible, "state_consistent": consistent, "reasons": reasons}

    def update(self, action: str, observation: str, model_output: str = "") -> Dict[str, object]:
        action = normalize(action)
        failed = action_failed(observation)

        previous_count = self.action_counts.get(action, 0)
        repeated = previous_count > 0
        self.action_counts[action] = previous_count + 1
        if repeated:
            self.repeated_actions += 1

        changed = False
        if failed:
            context = self._context_signature()
            self.state.contextual_failures.append(
                {"action": action, "context": context, "observation": " ".join(observation.split())}
            )
            prior_failures = self.failed_action_counts.get(action, 0)
            self.failed_action_counts[action] = prior_failures + 1
            if prior_failures > 0:
                self.repeated_failed_actions += 1
        else:
            changed = self._apply_success(action)
            self.state.contextual_failures = [
                item for item in self.state.contextual_failures if item["action"] != action
            ]

        if changed:
            current_context = self._context_signature()
            self.state.contextual_failures = [
                item for item in self.state.contextual_failures
                if item["context"] == current_context
            ]

        self.state.current_observation = " ".join(observation.split())
        self.pending_decision_point = changed

        return {
            "action_failed": failed,
            "repeated_action": repeated,
            "state_changed": changed,
            "state": self.snapshot(),
        }

    def _record_error(self, label: str) -> None:
        if label not in self.state_related_errors:
            self.state_related_errors.append(label)

    def snapshot(self) -> Dict[str, object]:
        return self.state.to_dict()

    def render_goal_reminder(self) -> str:
        return f"\nCURRENT TASK GOAL: {self.state.original_goal}\n"

    def render(self) -> str:
        inventory = "; ".join(self.state.inventory) or "None confirmed"
        conditions = "; ".join(
            f"{key}: {value}" for key, value in sorted(self.state.object_conditions.items())
        ) or "None confirmed"
        containers = "; ".join(
            f"{key}: {value}" for key, value in sorted(self.state.container_states.items())
        ) or "None confirmed"
        progress = "; ".join(self.state.confirmed_progress) or "None confirmed"
        failures = "; ".join(
            item["action"] for item in self.state.contextual_failures
        ) or "None in the current context"
        return (
            self.render_goal_reminder()
            + "CURRENT OBSERVABLE STATE (facts only; no recommended plan):\n"
            + f"- Location: {self.state.current_location}\n"
            + f"- Inventory: {inventory}\n"
            + f"- Object conditions: {conditions}\n"
            + f"- Container states: {containers}\n"
            + f"- Confirmed progress: {progress}\n"
            + f"- Context-relevant failed actions: {failures}\n"
            + f"- Latest observation: {self.state.current_observation}\n"
        )
