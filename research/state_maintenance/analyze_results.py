#!/usr/bin/env python3
"""Compare baseline, goal-reminder, and structured-state AgentBench runs."""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List


def _records(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    output = record.get("output") or {}
    result = output.get("result") or record.get("result") or {}
    experiment = result.get("experiment") or {}
    raw_success = result.get("result", 0)
    try:
        success = int(raw_success) == 1
    except (TypeError, ValueError):
        success = bool(raw_success)
    status = str(output.get("status") or record.get("status") or "unknown")
    failures = list(experiment.get("failure_types") or [])
    if status == "task limit reached" and "task_limit_exceeded" not in failures:
        failures.append("task_limit_exceeded")
    decisions = int(experiment.get("decision_points", 0))
    consistent = int(experiment.get("state_consistent_decisions", 0))
    return {
        "index": record.get("index"),
        "success": success,
        "status": status,
        "rounds": int(experiment.get("interaction_rounds", len(result.get("log") or []))),
        "repeated_actions": int(experiment.get("repeated_actions", 0)),
        "repeated_failed_actions": int(experiment.get("repeated_failed_actions", 0)),
        "decision_points": decisions,
        "state_consistent_decisions": consistent,
        "state_inconsistent_actions": int(experiment.get("state_inconsistent_actions", 0)),
        "failure_types": failures,
    }


def load_runs(path: Path) -> List[Dict[str, Any]]:
    return [normalize_record(record) for record in _records(path)]


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(rows)
    failures = Counter(item for row in rows for item in row["failure_types"])
    decision_points = sum(row["decision_points"] for row in rows)
    consistent = sum(row["state_consistent_decisions"] for row in rows)
    return {
        "tasks": count,
        "completed": sum(row["success"] for row in rows),
        "completion_rate": sum(row["success"] for row in rows) / count if count else 0.0,
        "task_limit_exceeded": failures["task_limit_exceeded"],
        "task_limit_rate": failures["task_limit_exceeded"] / count if count else 0.0,
        "average_rounds": mean(row["rounds"] for row in rows) if count else 0.0,
        "total_repeated_actions": sum(row["repeated_actions"] for row in rows),
        "total_repeated_failed_actions": sum(row["repeated_failed_actions"] for row in rows),
        "decision_points": decision_points,
        "state_consistent_decisions": consistent,
        "state_consistent_decision_rate": consistent / decision_points if decision_points else 0.0,
        "state_inconsistent_actions": sum(row["state_inconsistent_actions"] for row in rows),
        "failure_types": dict(failures),
    }


def paired_completion(first: List[Dict[str, Any]], second: List[Dict[str, Any]]) -> Dict[str, int]:
    first_by_index = {str(row["index"]): row for row in first}
    second_by_index = {str(row["index"]): row for row in second}
    common = sorted(set(first_by_index) & set(second_by_index))
    improved = regressed = unchanged = 0
    for index in common:
        before = first_by_index[index]["success"]
        after = second_by_index[index]["success"]
        if after and not before:
            improved += 1
        elif before and not after:
            regressed += 1
        else:
            unchanged += 1
    return {"matched_tasks": len(common), "improved": improved, "regressed": regressed, "unchanged": unchanged}


def write_task_csv(path: Path, conditions: Dict[str, List[Dict[str, Any]]]) -> None:
    fields = [
        "condition", "index", "success", "status", "rounds",
        "repeated_actions", "repeated_failed_actions", "decision_points",
        "state_consistent_decisions", "state_inconsistent_actions",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for condition, rows in conditions.items():
            for row in rows:
                writer.writerow({"condition": condition, **{key: row[key] for key in fields if key != "condition"}})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--goal-reminder", type=Path, required=True)
    parser.add_argument("--structured", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    args = parser.parse_args()

    conditions = {
        "baseline": load_runs(args.baseline),
        "goal_reminder": load_runs(args.goal_reminder),
        "structured": load_runs(args.structured),
    }
    summaries = {name: summarize(rows) for name, rows in conditions.items()}
    report = {
        "conditions": summaries,
        "paired_completion": {
            "goal_reminder_vs_baseline": paired_completion(conditions["baseline"], conditions["goal_reminder"]),
            "structured_vs_goal_reminder": paired_completion(conditions["goal_reminder"], conditions["structured"]),
            "structured_vs_baseline": paired_completion(conditions["baseline"], conditions["structured"]),
        },
        "interpretation_note": (
            "Completion is primary. Decision consistency is the main process measure. "
            "Repetition is descriptive and does not establish forgetting or planning quality."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comparison_summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    write_task_csv(args.output_dir / "task_level_results.csv", conditions)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
