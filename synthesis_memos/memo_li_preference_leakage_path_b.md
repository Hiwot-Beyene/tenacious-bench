# Path memo: Preference Leakage (Li et al., 2025) — Path B controls

## Claim we take seriously

If the same LM family **writes the preferred completion** and **judges** it, benchmarks (and internal offline metrics) can **overstate** alignment.

## Concrete control in this repo

- **Chosen default:** `data/tasks_train.jsonl` `candidate_output` after `evaluation/scoring_evaluator.py` passes—no generator involved.
- **Rejected:** deterministic mutators in `bench_corpus/preference_mutators.py`, verified with the same evaluator.
- **Future OpenRouter rewrites:** document **cross-family** rotation (e.g., DeepSeek rewrite vs Qwen judge) in `training_data/README.md` before spending eval-tier budget.

## Disagreement nuance

Not all “same vendor” models are equivalent families; the operational rule we enforce is **process isolation in the build log**, not only vendor string matching.
