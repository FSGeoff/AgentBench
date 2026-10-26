#!/usr/bin/env bash
set -u

PID_DIR="${HOME}/agentbench-logs/pids"

for pid_file in   "${PID_DIR}/alfworld-state-pilot-baseline.pid"   "${PID_DIR}/alfworld-state-pilot-goal-reminder.pid"   "${PID_DIR}/alfworld-state-pilot-structured.pid"   "${PID_DIR}/task-controller.pid"
do
  if [[ -f "$pid_file" ]]; then
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
      echo "Stopped process $pid"
    fi
  fi
done

echo "Pilot task services stopped."
echo "The Vicuna worker was left running. Stop it separately when all inference is finished."
