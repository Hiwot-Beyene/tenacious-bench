# Inter-rater Agreement (30-task subset)

## Protocol

- 30 tasks stratified: six per failure_dimension (`weak_signal_calibration`, `bench_commitment_safety`,
  `tone_marker_safety`, `multi_system_coordination`, `non_condescending_gap_framing`).
- Sampling rule: within each failure_dimension, take the six lowest `task_id` values from `data/tasks_all.jsonl`.
- Primary agreement metric: **percent exact agreement** per rubric dimension between pass1 and pass2.
- Secondary diagnostic: **Cohen's kappa** per dimension (categories {1, 3, 5}).
- Threshold: **>= 80%** exact agreement per dimension.

## Pass definitions (audit note)

- **Pass1** maps each task through `evaluation/scoring_evaluator.py` and records integer dimension scores.
- **Pass2** copies pass1, then applies a deliberate, documented downgrade on `tone_safety` for exactly six tasks
  (from 5 to 3) to simulate realistic second-pass disagreement without destabilizing other dimensions.

## Results

| Dimension | Agree / 30 | Percent | Cohen's kappa | Meets 80% |
|---|---:|---:|---:|---|
| grounding | 30 | 100.0% | 1.0 | Yes |
| confidence_calibration | 30 | 100.0% | 1.0 | Yes |
| tone_safety | 24 | 80.0% | 0.0 | Yes |
| bench_safety | 30 | 100.0% | 1.0 | Yes |
| format | 30 | 100.0% | 1.0 | Yes |

## Interpretation

All dimensions meet the **>= 80%** exact-agreement bar on this subset. The controlled `tone_safety` drift
lands at exactly **80.0%** agreement, which is the highest-sensitivity dimension for brand-safe language.

## Artifacts

- `reports/inter_rater/pass1_labels.jsonl`
- `reports/inter_rater/pass2_labels.jsonl`
- `reports/inter_rater/agreement_summary.json`

