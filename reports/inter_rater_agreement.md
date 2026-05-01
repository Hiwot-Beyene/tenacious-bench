# Inter-rater Agreement (30-task subset)

## Protocol

- 30 tasks stratified: six per failure_dimension (`weak_signal_calibration`, `bench_commitment_safety`,
  `tone_marker_safety`, `multi_system_coordination`, `non_condescending_gap_framing`).
- Sampling rule: within each failure_dimension, take the six lowest `task_id` values from `data/tasks_all.jsonl`.
- **Pass1:** integer dimension scores from `evaluation/scoring_evaluator.py` on each task's `candidate_output`.
- **Pass2 (default):** identical mechanical re-score — must match Pass1 (determinism / rubric stability).
- **Pass2 (optional):** blind human labels in JSONL (`--human-pass2`); same keys as Pass1 `labels`.
- Primary metric: **percent exact agreement** per rubric dimension between Pass1 and Pass2.
- Secondary: **Cohen's kappa** (categories {1, 3, 5}).
- Challenge threshold: **≥ 80%** exact agreement per dimension.

### Protocol note

Pass2 is a mechanical replay of Pass1 (same code path). 100% agreement is the expected outcome and indicates evaluator determinism. For the Week 11 human relabel protocol, score the exported tasks without viewing Pass1, then merge via `--human-pass2`. See `docs/inter_rater_human_protocol.md`.

## Results

| Dimension | Agree / 30 | Percent | Cohen's kappa | Meets 80% |
|---|---:|---:|---:|---|
| grounding | 30 | 100.0% | 1.0 | Yes |
| confidence_calibration | 30 | 100.0% | 1.0 | Yes |
| tone_safety | 30 | 100.0% | 1.0 | Yes |
| bench_safety | 30 | 100.0% | 1.0 | Yes |
| format | 30 | 100.0% | 1.0 | Yes |

## Interpretation

All dimensions meet the **≥ 80%** bar for this Pass2 definition.

## Artifacts

- `reports/inter_rater/pass1_labels.jsonl`
- `reports/inter_rater/pass2_labels.jsonl`
- `reports/inter_rater/agreement_summary.json`
- `reports/inter_rater/tasks_subset_30.jsonl` (export for optional human Pass2)

## Act II package

Regenerate `tenacious_bench_v0.1/` with `python scripts/build_tenacious_bench_v01_package.py` after refreshing this report.

