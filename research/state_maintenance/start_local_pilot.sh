#!/usr/bin/env bash
set -euo pipefail

: "${ALFWORLD_DATA:?Set ALFWORLD_DATA to the downloaded ALFWorld directory first.}"

LOG_DIR="${HOME}/agentbench-logs"
PID_DIR="${LOG_DIR}/pids"
mkdir -p "${PID_DIR}"

python - <<'PY'
import requests
response = requests.post(
    "http://127.0.0.1:55555/worker_generate_stream",
    json={
        "model": "vicuna-7b-v1.5",
        "prompt": "USER: Reply READY.\nASSISTANT:",
        "temperature": 0,
        "top_p": 1,
        "max_new_tokens": 8,
        "echo": False,
    },
    timeout=120,
)
response.raise_for_status()
print("Vicuna worker reachable")
PY

nohup python -m src.server.task_controller --port 5000   > "${LOG_DIR}/task-controller.log" 2>&1 &
echo $! > "${PID_DIR}/task-controller.pid"

python - <<'PY'
import time
import requests

url = "http://127.0.0.1:5000/api/list_workers"
for _ in range(30):
    try:
        if requests.get(url, timeout=2).ok:
            print("Task controller reachable")
            break
    except requests.RequestException:
        pass
    time.sleep(1)
else:
    raise SystemExit("Task controller did not start")
PY

start_worker() {
  local name="$1"
  local port="$2"
  nohup python -m src.server.task_worker "$name"     --self "http://127.0.0.1:${port}/api"     --port "$port"     --controller "http://127.0.0.1:5000/api"     > "${LOG_DIR}/${name}.log" 2>&1 &
  echo $! > "${PID_DIR}/${name}.pid"
}

start_worker alfworld-state-pilot-baseline 5001
start_worker alfworld-state-pilot-goal-reminder 5002
start_worker alfworld-state-pilot-structured 5003

python - <<'PY'
import time
import requests

url = "http://127.0.0.1:5000/api/list_workers"
for _ in range(60):
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        data = response.json()
        print("Registered task workers:", data)
        if len(str(data)) > 2:
            break
    except requests.RequestException:
        pass
    time.sleep(1)
else:
    raise SystemExit("Task workers did not register")
PY

echo "Local pilot services started. Run:"
echo "python -m src.assigner --config configs/assignments/alfworld_state_pilot.yaml"
