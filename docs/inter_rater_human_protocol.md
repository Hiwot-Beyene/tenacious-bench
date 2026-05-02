# Human inter-rater protocol (optional Pass2)

Use this when you need **blind human relabels** to satisfy the Week 11 narrative:
**30-task subset**, **two passes at least 24 hours apart**, second pass **blind to first-pass labels**,
**≥80% exact agreement per dimension** (or **Tenacious-Bench scorer** revision per `docs/rubric_revision_log.md`).

## Steps

### Pass 1 (day/session 1)

1. Run `python scripts/compute_inter_rater_agreement.py` once to generate
   `reports/inter_rater/tasks_subset_30.jsonl` and (for export only) Pass1 machine labels.
2. **Human raters:** work **only** from `tasks_subset_30.jsonl` + `evaluation/scoring_evaluator.py`
   dimension definitions. **Do not open** `reports/inter_rater/pass1_labels.jsonl` if you are
   producing an independent human Pass1 file; for the repo’s mechanical baseline, Pass1 is the scorer output.

3. For each task in `tasks_subset_30.jsonl`, read `candidate_output` and assign
   integer scores **{1, 3, 5}** for each dimension, using the same definitions as
   `evaluation/scoring_evaluator.py` (grounding, confidence_calibration, tone_safety,
   bench_safety, format).

4. Write one JSON object per line to a new file, e.g. `reports/inter_rater/human_pass1.jsonl`:

   ```json
   {"task_id": "tb_v01_000001", "labels": {"grounding": 5, "confidence_calibration": 5, "tone_safety": 5, "bench_safety": 5, "format": 5}}
   ```

### Pass 2 (day/session 2, ≥24h later)

5. **Without** viewing Pass 1 labels, repeat scoring from the **same** `tasks_subset_30.jsonl`
   (fresh read of emails only). Write `reports/inter_rater/human_pass2.jsonl`:


   ```json
   {"task_id": "tb_v01_000001", "labels": {"grounding": 5, "confidence_calibration": 5, "tone_safety": 5, "bench_safety": 5, "format": 5}}
   ```

6. Merge with the committed Pass1 baseline (or compare two human files) using:

   ```bash
   python scripts/compute_inter_rater_agreement.py --human-pass2 reports/inter_rater/human_pass2.jsonl
   ```

   (Extend the script if you need Pass1-from-human vs Pass2-from-human; the default compares mechanical Pass1 to `human_pass2`.)

7. If any dimension falls below 80%, follow **`docs/rubric_revision_log.md`**, revise **this benchmark’s** scorer text in
   `scoring_evaluator.py` / methodology, then **re-label the same 30 tasks** after a cooldown.

## Mechanical baseline

With `--human-pass2` omitted, Pass2 is a **mechanical replay** of Pass1. Agreement
should be **100%** and documents that the committed evaluator is deterministic.
