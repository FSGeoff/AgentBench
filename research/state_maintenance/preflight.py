#!/usr/bin/env python3
"""CPU-only consistency checks for the three-condition experiment."""

import json
from pathlib import Path
from typing import Dict, List
import yaml

ROOT = Path(__file__).resolve().parents[2]


def flatten_split(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError(f"{path} must contain a non-empty object")
    tasks = []
    for category, values in data.items():
        if not isinstance(values, list) or not values:
            raise ValueError(f"Category {category!r} in {path} must contain tasks")
        tasks.extend(values)
    if len(tasks) != len(set(tasks)):
        raise ValueError(f"{path} contains duplicate tasks")
    return tasks


def task_definitions() -> Dict[str, dict]:
    return yaml.safe_load((ROOT / "configs/tasks/alfworld.yaml").read_text(encoding="utf-8"))


def check_conditions(definitions: Dict[str, dict], names: List[str], split: str) -> None:
    expected_modes = ["baseline", "goal_reminder", "structured"]
    for name, mode in zip(names, expected_modes):
        parameters = definitions[name]["parameters"]
        if parameters["split"] != split:
            raise ValueError(f"{name} must use split {split}")
        if parameters["state_mode"] != mode:
            raise ValueError(f"{name} must use state_mode {mode}")


def run_checks() -> Dict[str, int]:
    pilot = flatten_split(ROOT / "data/alfworld/research_pilot_4.json")
    full = flatten_split(ROOT / "data/alfworld/research_24.json")
    if len(pilot) != 4 or len(full) != 24:
        raise ValueError("Expected 4 pilot tasks and 24 full tasks")
    if not set(pilot).issubset(full):
        raise ValueError("Every pilot task must occur in the full split")

    definitions = task_definitions()
    check_conditions(
        definitions,
        [
            "alfworld-state-pilot-baseline",
            "alfworld-state-pilot-goal-reminder",
            "alfworld-state-pilot-structured",
        ],
        "research_pilot_4",
    )
    check_conditions(
        definitions,
        [
            "alfworld-state-baseline",
            "alfworld-state-goal-reminder",
            "alfworld-state-structured",
        ],
        "research_24",
    )
    return {"pilot_tasks": len(pilot), "full_tasks": len(full), "conditions": 3}


if __name__ == "__main__":
    print("Preflight passed:", json.dumps(run_checks(), sort_keys=True))
