# AgentBench ALFWorld Current-State Extension

This extension tests whether organizing already-observed facts into a compact current-state record improves next-subgoal decisions and task completion in AgentBench House Holding tasks.

## Revised research question

When current facts and prior progress already appear in the conversation history, does a compact current-state record improve the agent's next-subgoal decisions and task completion?

## Focal decision

The focal decision occurs after ALFWorld confirms a meaningful state change. The model must choose an action that is consistent with the current state and advances an unfinished part of the goal. Examples include selecting the next task phase after acquiring an object or changing its condition.

Repeated actions do not establish forgetting. The model may remember the prior outcome yet lack a better plan or misunderstand the environment.

## Three matched conditions

- `alfworld-state-baseline`: standard AgentBench conversation history.
- `alfworld-state-goal-reminder`: the same history plus the original goal repeated before each action.
- `alfworld-state-structured`: the same goal reminder plus a compact current-state record.

The goal-reminder control separates the value of repeating the goal from the added value of organizing current facts. The structured record contains no recommended next action and no model-generated remaining plan.

All conditions use the same model, fixed tasks, demonstrations, temperature, 35-round limit, and environment configuration.

## Current-state fields

The structured condition displays only observable information:

- Current location
- Current inventory
- Confirmed object conditions
- Confirmed container states
- Latest observation
- Confirmed goal-relevant progress
- Context-relevant failed actions

A newer confirmed fact replaces the prior displayed fact for the same entity. Superseded facts remain in logs for audit but are not shown to the model. Failed actions expire when their relevant context changes or the action later succeeds.

## Evaluation

Primary outcome:

- Task-completion rate

Main process outcome:

- State-consistent next-subgoal decision rate at predefined decision points

Supporting descriptive outcomes:

- Task Limit Exceeded rate
- Interaction rounds
- Invalid actions
- Repeated and repeated-failed actions
- State-contradictory actions
- Recovery after unsuccessful actions

Better completion shows that the aid is useful in this setting. A higher state-consistent decision rate supports a narrower claim that explicit current state helps the model select the next subgoal. Neither outcome proves that the model forgot information.

## Scope

The full study uses 24 fixed tasks, with four from each ALFWorld task type, in all three conditions. The pilot uses four tasks in each condition.

Even a perfectly accurate record cannot supply planning skill, causal knowledge, or correct understanding of ALFWorld rules. The model can possess the correct state and still choose an ineffective action.

## Files

- `data/alfworld/research_24.json`: fixed full split
- `data/alfworld/research_pilot_4.json`: fixed pilot
- `src/server/tasks/alfworld/state_tracker.py`: observable current-state tracker
- `configs/tasks/alfworld.yaml`: three matched task definitions
- `configs/assignments/alfworld_state_experiment.yaml`: full experiment
- `configs/assignments/alfworld_state_pilot.yaml`: pilot
- `research/state_maintenance/EXPERIMENT_PROTOCOL.md`: formal protocol
- `research/state_maintenance/DECISION_RUBRIC.md`: trajectory annotation rubric
- `research/state_maintenance/analyze_results.py`: three-condition comparison
- `tests/state_maintenance/`: CPU-only tests

## CPU-only checks

```bash
python -m unittest discover -s tests/state_maintenance -v
python research/state_maintenance/preflight.py
```

## Pilot

```bash
python -m src.assigner -c configs/assignments/alfworld_state_pilot.yaml
```

The pilot is a systems check and should not be reported as the final result.

## Full experiment

```bash
python -m src.assigner -c configs/assignments/alfworld_state_experiment.yaml
```

After all three conditions finish:

```bash
python research/state_maintenance/analyze_results.py \
  --baseline outputs/EXPERIMENT/vicuna-7b/alfworld-state-baseline/runs.jsonl \
  --goal-reminder outputs/EXPERIMENT/vicuna-7b/alfworld-state-goal-reminder/runs.jsonl \
  --structured outputs/EXPERIMENT/vicuna-7b/alfworld-state-structured/runs.jsonl \
  --output-dir outputs/EXPERIMENT/state-analysis
```
