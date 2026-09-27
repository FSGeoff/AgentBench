# AgentBench ALFWorld State-Maintenance Extension

This extension tests one question: **Does an explicit structured task-state
summary improve an LLM agent's performance on multi-round ALFWorld tasks?**

![AgentBench ALFWorld state-maintenance workflow](agentbench_state_workflow.svg)

See [`WORKFLOW.md`](WORKFLOW.md) for a step-by-step explanation of how
AgentBench, the LLM, ALFWorld, the state tracker, and result analysis interact.

The experiment compares two matched conditions:

- `alfworld-state-baseline`: the unmodified AgentBench conversation-history approach.
- `alfworld-state-structured`: the same model, tasks, prompt examples,
  temperature, and 35-round limit, plus a compact state summary before each action.

The summary contains the original goal, latest observation, confirmed successful
actions, failed actions, and the agent's latest stated plan. It is constructed
only from information visible to the agent. No hidden ALFWorld state or solution
path is used.

## Files added or changed

- `data/alfworld/research_24.json`: fixed task split with four tasks from each
  of ALFWorld's six task types.
- `src/server/tasks/alfworld/state_tracker.py`: observable-only state tracker.
- `configs/tasks/alfworld.yaml`: matched baseline and structured task definitions.
- `configs/assignments/alfworld_state_experiment.yaml`: reproducible assignment.
- `research/state_maintenance/analyze_results.py`: paired comparison and summaries.
- `research/state_maintenance/EXPERIMENT_PROTOCOL.md`: run and reporting protocol.
- `tests/state_maintenance/`: tests that do not require a GPU or ALFWorld image.

## Setup

1. Check out branch `research/state-maintenance-v0.2`.
2. Install the v0.2 dependencies: `pip install -r requirements.txt`.
3. Install Docker and pull `longinyu/agentbench-alfworld`.
4. Configure one open-source instruction-following model in
   `configs/agents/fs_agent.yaml`. The supplied assignment uses `vicuna-7b`;
   substitute another single model only before collecting either condition.
5. Keep decoding deterministic (`temperature: 0`) and do not change the model,
   task split, prompt examples, or maximum steps between conditions.

The framework does not train a model. GPU access is needed only for local model
inference; the tracker, analysis, and unit tests run on CPU.

## CPU-only checks

```bash
python -m unittest discover -s tests/state_maintenance -v
python research/state_maintenance/preflight.py
```

## Run the pilot first

The pilot uses four tasks in each condition—eight task executions total—with
the existing `vicuna-7b` agent definition. After starting the task and model
services, run:

```bash
python -m src.assigner -c configs/assignments/alfworld_state_pilot.yaml
```

Use the pilot to confirm that both conditions finish, create `runs.jsonl`, and
contain the additional experiment fields. Pilot results are a systems check and
should not be reported as the final study findings.

## Run the full experiment

Start the AgentBench task services, then run:

```bash
python -m src.assigner -c configs/assignments/alfworld_state_experiment.yaml
```

After both conditions finish, locate their `runs.jsonl` files and compare them:

```bash
python research/state_maintenance/analyze_results.py \
  --baseline outputs/EXPERIMENT/vicuna-7b/alfworld-state-baseline/runs.jsonl \
  --structured outputs/EXPERIMENT/vicuna-7b/alfworld-state-structured/runs.jsonl \
  --output-dir outputs/EXPERIMENT/state-analysis
```

The script produces `comparison_summary.json` and `task_level_results.csv`.
