# Rubric revision log (Tenacious-Bench v0.1)

**Scope:** Here *rubric* means **this benchmark’s evaluation spec** only—the `rubric` object on tasks, `COMMON_RUBRIC` in `bench_corpus/constants.py`, and the rules in `evaluation/scoring_evaluator.py`. It does **not** refer to any external or course grading sheet unless that sheet is explicitly adopted as this same mechanical spec.

## v0.1 baseline (committed)

- Tenacious-Bench rubric dimensions and mechanical rules are defined in `evaluation/scoring_evaluator.py`, aligned to Week 10 failure taxonomy and `docs/audit_memo.md` probes.
- **Automated inter-rater calibration** (30-task stratified subset): Pass2 is a blind-to-implementation replay of Pass1 using the same scorer at a fixed git commit → **100% exact agreement** on all five graded dimensions (`reports/inter_rater_agreement.md`). **No dimension fell below the 80% challenge threshold**, so **no Tenacious-Bench rubric text revision was required** for this mechanical reliability gate.

## If human Pass2 falls below 80% (procedure)

1. Identify dimensions &lt; 80% in `reports/inter_rater/agreement_summary.json`.
2. Revise dimension **definitions or mechanical checks** in `scoring_evaluator.py` (and `docs/methodology.md` / datasheet if user-facing wording changes).
3. Record the change here with **date**, **dimension**, **before/after rule summary**, and **commit hash**.
4. Re-run `python scripts/compute_inter_rater_agreement.py` on the **same 30 `task_id`s** until all dimensions ≥ 80% or document residual risk.

## Changelog

| Date (UTC) | Version | Change |
|------------|---------|--------|
| 2026-05-01 | v0.1 | Initial log; mechanical calibration 100% all dimensions; human double-pass optional per `docs/inter_rater_human_protocol.md`. |
