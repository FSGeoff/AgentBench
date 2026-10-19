# AgentBench ALFWorld Experiment Workflow

## Purpose

AgentBench coordinates three matched ALFWorld conditions. The extension tests whether a compact current-state record improves next-subgoal decisions after confirmed state changes.

## Conditions

- Baseline receives standard conversation history.
- Goal-reminder receives the same history plus the original goal before each action.
- Structured state receives the same goal reminder plus current observable state.

The third condition contains no recommended next action or generated plan.

## Interaction cycle

1. AgentBench sends the task, observation, and admissible actions.
2. The LLM selects one action.
3. ALFWorld executes it and returns visible feedback.
4. The tracker updates current fields and marks replaced values as superseded.
5. AgentBench logs whether the next action conflicts with known current state.
6. The loop continues until success or a finish condition.

## Staleness policy

Current fields replace rather than accumulate. A newer location, inventory fact, object condition, or container state supersedes its prior value. Context-bound failures leave the displayed record when their preconditions change or the action later succeeds.

The full trajectory and superseded values remain available to the researcher but are not shown to the LLM.

## Focal decision

After a meaningful state change, the model must select the next unfinished subgoal. Manual blinded review scores whether the following action is consistent with current state and directed toward remaining task requirements.

Automatic contradiction rules can identify obvious cases, such as trying to take an object already held. They cannot determine whether every legal action reflects a good plan.

## Termination

A run ends when ALFWorld reports success, the model produces an invalid format or action, the context limit is reached, a repeated-action loop triggers the existing AgentBench stop rule, or 35 rounds elapse.

## Analysis

The analysis compares completion across all three conditions. It then compares state-consistent next-subgoal decisions, followed by timeouts, rounds, invalid actions, and repetition as descriptive measures.

Reduced repetition alone will not support a planning or forgetting claim. Even a perfect state record cannot make an agent understand environment rules or form an effective plan.
