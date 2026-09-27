#!/usr/bin/env python3
"""CPU-only consistency checks for the state-maintenance experiment."""

import argparse
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
    path = ROOT / "configs/tasks/alfworld.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_pair(definitions: Dict[str, dict], baseline_name: str, structured_name: str, split: str) -> None:
    baseline = definitions[baseline_name]["parameters"]
    structured = definitions[structured_name]["parameters"]
    if baseline["split"] != split or structured["split"] != split:
        raise ValueError(f"Both conditions must use split {split}")
    if baseline["state_mode"] != "baseline":
        raise ValueError(f"{baseline_name} must use baseline state_mode")
    if structured["state_mode"] != "structured":
        raise ValueError(f"{structured_name} must use structured state_mode")


def run_checks() -> Dict[str, int]:
    pilot = flatten_split(ROOT / "data/alfworld/research_pilot_4.json")
    full = flatten_split(ROOT / "data/alfworld/research_24.json")
    if len(pilot) != 4:
        raise ValueError(f"Pilot split must contain 4 tasks; found {len(pilot)}")
    if len(full) != 24:
        raise ValueError(f"Full split must contain 24 tasks; found {len(full)}")
    if not set(pilot).issubset(full):
        raise ValueError("Every pilot task must also occur in the full split")

    definitions = task_definitions()
    check_pair(definitions, "alfworld-state-pilot-baseline", "alfworld-state-pilot-structured", "research_pilot_4")
    check_pair(definitions, "alfworld-state-baseline", "alfworld-state-structured", "research_24")
    return {"pilot_tasks": len(pilot), "full_tasks": len(full), "conditions": 2}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    report = run_checks()
    print("Preflight passed:", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
