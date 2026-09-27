#!/usr/bin/env python3
"""Compare matched baseline and structured-state AgentBench run files."""

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
    return {
        "index": record.get("index"),
        "success": success,
        "status": status,
        "rounds": int(experiment.get("interaction_rounds", len(result.get("log") or []))),
        "repeated_actions": int(experiment.get("repeated_actions", 0)),
        "repeated_failed_actions": int(experiment.get("repeated_failed_actions", 0)),
        "state_related_errors": list(experiment.get("state_related_errors") or []),
        "failure_types": failures,
    }


def load_runs(path: Path) -> List[Dict[str, Any]]:
    return [normalize_record(record) for record in _records(path)]


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(rows)
    failures = Counter(item for row in rows for item in row["failure_types"])
    state_errors = Counter(item for row in rows for item in row["state_related_errors"])
    return {
        "tasks": count,
        "completed": sum(row["success"] for row in rows),
        "completion_rate": sum(row["success"] for row in rows) / count if count else 0.0,
        "task_limit_exceeded": failures["task_limit_exceeded"],
        "task_limit_rate": failures["task_limit_exceeded"] / count if count else 0.0,
        "average_rounds": mean(row["rounds"] for row in rows) if count else 0.0,
        "total_repeated_actions": sum(row["repeated_actions"] for row in rows),
        "average_repeated_actions": mean(row["repeated_actions"] for row in rows) if count else 0.0,
        "total_repeated_failed_actions": sum(row["repeated_failed_actions"] for row in rows),
        "failure_types": dict(failures),
        "state_related_errors": dict(state_errors),
    }


def paired_comparison(baseline: List[Dict[str, Any]], structured: List[Dict[str, Any]]) -> Dict[str, int]:
    base_by_index = {str(row["index"]): row for row in baseline}
    state_by_index = {str(row["index"]): row for row in structured}
    common = sorted(set(base_by_index) & set(state_by_index))
    improved = regressed = unchanged = 0
    for index in common:
        before = base_by_index[index]["success"]
        after = state_by_index[index]["success"]
        if after and not before:
            improved += 1
        elif before and not after:
            regressed += 1
        else:
            unchanged += 1
    return {"matched_tasks": len(common), "improved": improved, "regressed": regressed, "unchanged": unchanged}


def write_task_csv(path: Path, baseline: List[Dict[str, Any]], structured: List[Dict[str, Any]]) -> None:
    fields = ["condition", "index", "success", "status", "rounds", "repeated_actions", "repeated_failed_actions"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for condition, rows in (("baseline", baseline), ("structured", structured)):
            for row in rows:
                writer.writerow({"condition": condition, **{key: row[key] for key in fields if key != "condition"}})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline runs.jsonl")
    parser.add_argument("--structured", type=Path, required=True, help="Structured-state runs.jsonl")
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    args = parser.parse_args()

    baseline = load_runs(args.baseline)
    structured = load_runs(args.structured)
    report = {
        "baseline": summarize(baseline),
        "structured": summarize(structured),
        "paired": paired_comparison(baseline, structured),
    }
    report["differences_structured_minus_baseline"] = {
        key: report["structured"][key] - report["baseline"][key]
        for key in ("completion_rate", "task_limit_rate", "average_rounds", "average_repeated_actions")
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "comparison_summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_task_csv(args.output_dir / "task_level_results.csv", baseline, structured)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
