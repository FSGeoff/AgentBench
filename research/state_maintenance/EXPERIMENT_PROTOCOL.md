# Experiment Protocol

## Research question

Does providing an LLM agent with an explicit structured task-state summary
improve performance on multi-round AgentBench House Holding tasks?

## Design

Use one open-source instruction-following model and the same 24 ALFWorld tasks
in both conditions. The split contains four fixed tasks from each of the six
ALFWorld task categories. Run the baseline and structured conditions with the
same model checkpoint, inference server, temperature (`0`), maximum new tokens,
prompt examples, maximum rounds (`35`), and hardware.

The independent variable is whether the current structured state summary is
included in the user message. The summary is removed from older turns when a
new summary is supplied, preventing stale summaries from accumulating.

## Measures

Primary measure:

- Task-completion rate.

Secondary measures:

- Task Limit Exceeded count and rate.
- Total and average repeated actions.
- Repeated failed actions.
- Average interaction rounds.
- Deterministically identifiable failure and state-error labels.

## Procedure

1. Record the model name, exact checkpoint/revision, GPU, VRAM, software
   versions, and experiment date.
2. Run the CPU-only tests before using the GPU.
3. Confirm that both task definitions load `research_24.json` and contain 24 indices.
4. Start the model server once and do not alter its settings between conditions.
5. Run both conditions. Preserve the raw `runs.jsonl`, `overall.json`, and logs.
6. Run `analyze_results.py` on the two `runs.jsonl` files.
7. Inspect any missing or duplicate task indices before interpreting results.
8. Manually review trajectories labeled `repeated_action` or
   `repeated_failed_action`; record manual judgments separately from automatic labels.

## Interpretation rules

Treat this as a small, controlled extension rather than a new general
benchmark. Report raw counts with percentages. A higher completion rate and
lower task-limit/repetition measures support the hypothesis, but mixed results
should be reported as mixed. Do not claim statistical or cross-model
generalization from 24 tasks and one model.

The structured condition adds prompt tokens and may change behavior because of
formatting or increased attention, not memory alone. Report this as a confound.
The tracked "remaining steps" are the model's latest expressed plan, not a
ground-truth plan. Automated state-error labels are reproducible indicators,
not proof of an internal cognitive failure.

## Reproducibility record

Complete this before the final run:

- AgentBench branch and commit:
- Model/checkpoint and revision:
- Inference software and version:
- GPU and VRAM:
- Python and Docker versions:
- Run date:
- Random seed, if applicable:
- Output directory:
