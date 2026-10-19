# Next-Subgoal Decision Rubric

## Unit of analysis

Score the first agent action after a confirmed task-relevant state change. Examples include a successful pickup, location change, object transformation, container-state change, or placement.

Remove condition labels and state-record text from the reviewer copy when practical so the reviewer does not know which experimental condition produced the trajectory.

## Question 1: State consistency

Does the action agree with current observable facts?

- **1 Consistent:** The action does not contradict the latest confirmed location, inventory, object condition, or container state.
- **0 Inconsistent:** The action assumes a fact that the visible trajectory contradicts.
- **NA Unclear:** The available observations do not support a reliable judgment.

Examples of inconsistency include trying to take an object already held, opening a container already confirmed open, or acting as if the agent remains in a prior location.

## Question 2: Progress direction

Does the action attempt to advance an unfinished goal condition?

- **1 Progress-directed:** The action moves toward a requirement that the trajectory has not yet confirmed.
- **0 Not progress-directed:** The action revisits confirmed progress, pursues an unrelated object, or has no plausible connection to an unfinished requirement.
- **NA Unclear:** Several actions remain reasonable and the trajectory does not support a reliable judgment.

## Combined outcome

Count a next-subgoal decision as successful only when both questions receive a score of 1. Exclude NA decisions from the rate denominator and report the number excluded.

## Reviewer notes

For each 0 or NA score, quote the relevant prior observation and briefly explain the judgment. Do not infer that the model forgot information. Describe only the relationship between the selected action and the observable state.

## Reliability

If a second reviewer is available, independently score at least 20 percent of decision points and report agreement. Resolve disagreements after recording the original scores.
