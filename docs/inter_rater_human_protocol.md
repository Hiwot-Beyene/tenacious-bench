# Human inter-rater protocol (optional Pass2)

Use this when you need **blind human relabels** to satisfy the Week 11 narrative
(two passes, ≥80% agreement per dimension).

## Steps

1. Run `python scripts/compute_inter_rater_agreement.py` once to generate
   `reports/inter_rater/tasks_subset_30.jsonl` and mechanical Pass1 labels.
2. **Do not open** `reports/inter_rater/pass1_labels.jsonl` before labeling.
3. For each task in `tasks_subset_30.jsonl`, read `candidate_output` and assign
   integer scores **{1, 3, 5}** for each dimension, using the same definitions as
   `evaluation/scoring_evaluator.py` (grounding, confidence_calibration, tone_safety,
   bench_safety, format).
4. Write one JSON object per line to a new file, e.g. `reports/inter_rater/human_pass2.jsonl`:

   ```json
   {"task_id": "tb_v01_000001", "labels": {"grounding": 5, "confidence_calibration": 5, "tone_safety": 5, "bench_safety": 5, "format": 5}}
   ```

5. After ≥24h (or a second session), re-run agreement with:

   ```bash
   python scripts/compute_inter_rater_agreement.py --human-pass2 reports/inter_rater/human_pass2.jsonl
   ```

6. If any dimension falls below 80%, revise rubric text in `scoring_evaluator.py` /
   methodology, then repeat on the same 30 tasks.

## Mechanical baseline

With `--human-pass2` omitted, Pass2 is a **mechanical replay** of Pass1. Agreement
should be **100%** and documents that the committed evaluator is deterministic.
