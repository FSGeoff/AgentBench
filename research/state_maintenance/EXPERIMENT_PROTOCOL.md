# Experiment Protocol

## Research question

When current facts and prior progress already appear in the conversation history, does a compact current-state record improve the agent's next-subgoal decisions and task completion?

## Hypothesis

The structured condition will produce higher completion and a higher rate of state-consistent next-subgoal decisions than both the baseline and goal-reminder conditions.

Repeated action counts are descriptive and will not be treated as evidence of forgetting or improved planning.

## Design

Use one open-source instruction-following model and the same 24 fixed ALFWorld tasks in three conditions:

1. Baseline conversation history
2. Baseline history plus a repeated goal reminder
3. The same goal reminder plus a structured current-state record

Hold the model checkpoint, inference server, temperature, maximum new tokens, demonstrations, maximum rounds, hardware, and task order constant.

The goal-reminder comparison controls for assistance supplied by repeating the goal. The structured record contains no recommended action and no model-generated plan.

## Focal decision and decision points

The focal decision is the next-subgoal choice after a confirmed state change. A decision point occurs after an action changes a task-relevant state, including location, inventory, object condition, container state, or goal progress.

The following action is scored for:

- State consistency: it does not contradict current observable facts.
- Progress direction: it attempts to advance an unfinished goal condition.

Use `DECISION_RUBRIC.md` for blinded trajectory review. Automatic contradiction flags supplement rather than replace manual review.

## Preventing obsolete information

The tracker maintains one current value per entity and state attribute. A newer confirmed fact supersedes the prior displayed value. Superseded values remain in the audit log but do not appear in the prompt.

Failed actions are context-bound. Remove a displayed failure when the relevant location, inventory, or container state changes, or when the action later succeeds. If a previously satisfied goal condition becomes false, return it to pending.

The tracker may use only visible observations, chosen actions, and the original task. It may not read hidden simulator state or expert plans.

## Measures

Primary:

- Task-completion rate

Main process measure:

- State-consistent next-subgoal decision rate

Supporting descriptive measures:

- Task Limit Exceeded rate
- Interaction rounds
- Invalid actions
- Repeated and repeated-failed actions
- State-contradictory actions
- Recovery after an unsuccessful action

## Procedure

1. Record model, checkpoint, GPU, VRAM, software versions, and date.
2. Run CPU-only tests and preflight.
3. Run the four-task pilot in all three conditions.
4. Verify output fields and state replacement behavior.
5. Start the model server once and preserve all inference settings.
6. Run all three full conditions on the same 24 tasks.
7. Preserve raw trajectories, state snapshots, superseded facts, and logs.
8. Create a blinded annotation sheet without condition labels.
9. Score predefined decision points with the decision rubric.
10. Run the analysis script and inspect missing or duplicate task indices.
11. Report completion first, then decision quality, then descriptive behavior.

## Interpretation rules

Higher completion supports the usefulness of the aid in this setting. A structured-condition advantage over the goal-reminder control provides evidence that organization contributes beyond repeating the goal. The study cannot fully isolate token count, formatting, or attention effects.

A higher next-subgoal decision rate supports improved use of current facts at defined decision points. Reduced repetition alone does not establish better planning and does not prove forgetting.

Even a perfectly accurate state record cannot supply causal knowledge, planning competence, or correct understanding of ALFWorld affordances. Limit conclusions to one model, one environment, and 24 tasks.

## Reproducibility record

- AgentBench branch and commit:
- Model checkpoint and revision:
- Inference software and version:
- GPU and VRAM:
- Python and Docker versions:
- Run date:
- Random seed, if applicable:
- Output directory:
- Annotation reviewer:
- Blinding procedure:
