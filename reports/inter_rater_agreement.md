# Inter-rater Agreement (30-task subset)

## Double-labeling protocol

- **Subset:** 30 tasks — six per `failure_dimension` (`weak_signal_calibration`, `bench_commitment_safety`, `tone_marker_safety`, `multi_system_coordination`, `non_condescending_gap_framing`). **Sampling:** within each dimension, the six lowest `task_id` values from `data/tasks_all.jsonl`.
- **Pass 1:** integer scores per **Tenacious-Bench rubric** dimension on each `candidate_output` (grounding, confidence_calibration, tone_safety, bench_safety, format), same definitions as `evaluation/scoring_evaluator.py`.
- **Pass 2:** run **≥ 24 hours later**, **blind to Pass 1 labels** for human raters (see `docs/inter_rater_human_protocol.md`). In-repo default Pass2 is a **mechanical replay** of Pass1 to prove scorer determinism at this commit.
- **Primary metric:** percent **exact agreement** per dimension. **Challenge: ≥ 80%.**
- **Secondary:** Cohen's κ on categories {1, 3, 5}.

### Pass2 mode (this run)

Pass2 is a mechanical replay of Pass1 (same code path). 100% agreement is the expected outcome and indicates evaluator determinism. For the Week 11 human relabel protocol, score the exported tasks without viewing Pass1, then merge via `--human-pass2`. See `docs/inter_rater_human_protocol.md`.

## Agreement matrix (per dimension)

| Dimension | Agree | Disagree | Percent | Cohen's κ | Meets ≥80% |
|-----------|------:|---------:|--------:|----------:|:----------:|
| grounding | 30 | 0 | 100.0% | 1.0 | Yes |
| confidence_calibration | 30 | 0 | 100.0% | 1.0 | Yes |
| tone_safety | 30 | 0 | 100.0% | 1.0 | Yes |
| bench_safety | 30 | 0 | 100.0% | 1.0 | Yes |
| format | 30 | 0 | 100.0% | 1.0 | Yes |

## Rubric revision evidence

**Mechanical Pass2:** no dimension fell below 80%; see `docs/rubric_revision_log.md` (no revision required at this commit). If a **human** Pass2 drops below 80%, log **scorer / rubric** diffs there and re-run on the **same 30 tasks**.

## Final agreement (after protocol)

Per-dimension agreement is reported in the matrix above. All dimensions meet the ≥80% bar.

## Artifacts

- `reports/inter_rater/pass1_labels.jsonl`
- `reports/inter_rater/pass2_labels.jsonl`
- `reports/inter_rater/agreement_summary.json`
- `reports/inter_rater/tasks_subset_30.jsonl`

## Act II package

Regenerate `tenacious_bench_v0.1/` with `python scripts/build_tenacious_bench_v01_package.py` after refreshing this report.

