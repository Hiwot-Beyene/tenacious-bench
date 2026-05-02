# Methodology: Tenacious-Bench v0.1 (Act II complete)

## 1) Declared Training Path

**Path B — Preference-tuned judge/critic**.

Why Path B (not A/C) from Week 10 evidence:
- Week 10 shows repeated cases where pipeline execution succeeded while policy-safe sales behavior still required stricter filtering. Example traces: `3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95`, `85724927-681b-47b5-ba65-a13d705084c6`, `0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac`.
- This is a **consistency/decision-quality** profile, not only a text-generation profile. The required intervention is a critic that can reject unsafe outputs (over-assertion, over-commitment, condescension) even when language quality is high.
- Path B best matches that profile and is cheaper/faster to harden for interim deliverables.

## 2) Reading-Informed Design Choices

We anchor the design to required reading:
- **Gu et al. (LLM-as-a-Judge Survey)**: we decompose scoring into mechanically checkable dimensions plus bounded judge components; we do not rely on a single opaque score.
- **Li et al. (Preference Leakage)**: Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge.* arXiv:2502.01534. Generation and judging must rotate model families so the same model does not author and judge the same example (operationalized in `generation/model_routing.py` + `generation/routing_policy.md`).
- **Gebru et al. + Pushkarna et al.**: documentation is treated as a first-class artifact (datasheet with layered detail).

### Short Path Comparison (Why B over A/C)

**Path B chosen (critic/judge tuning)** is the best fit for the observed failure pattern:
- Week 10 traces show decision inconsistency under weak signals and bench-commitment risk (trace IDs: `3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95`, `85724927-681b-47b5-ba65-a13d705084c6`, `0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac`).
- Per **Gu et al. (2024/2025)**, decomposed evaluator dimensions are more reliable than single scalar judgment for production gating; this directly supports a critic layer.
- Per **Li et al. (2025)**, preference leakage can inflate judge confidence; our rotated generator/judge policy is a Path B control, not a Path A generation fix.

Why not Path A first:
- Path A (SFT generation) mainly improves writing style and phrasing quality, but our highest-severity misses are acceptance/rejection decisions on uncertain evidence.

Why not Path C first:
- Path C (process reward) is valuable for long-horizon trajectory supervision, but interim evidence points to immediate output-level gating needs with lower implementation cost in Week 11.

## 3) Partitioning Protocol (50/30/20)

Target dataset size: 200–300 tasks.

Partitioning:
- **Train 50%**: used for critic preference tuning.
- **Dev 30%**: public, used for Tenacious-Bench scorer / debug iteration.
- **Held-out 20%**: sealed for final reporting.

Stratification logic:
- Primary strata are Week 10 failure dimensions from `probes/failure_taxonomy.md` (ICP integrity, signal reliability, bench alignment, tone/brand safety, coordination, pricing/cost, scheduling/global logistics, competitive-gap rigor, stakeholder engagement).
- Each partition preserves category distribution so no single split over-represents one failure type.
- Within category, source-mode quotas are tracked: trace-derived, programmatic sweep, multi-LLM synthesis, hand-authored adversarial.

## 4) Contamination Checks (committed pipeline)

Canonical script: `generation/contamination_check.py` (CLI: `python scripts/run_contamination_check.py`).
Report: `reports/contamination_check.json` (schema **1.2**; copied into `tenacious_bench_v0.1/` by the package builder).

**Why inputs differ from a naive n-gram benchmark:** scenario templates repeat across splits; an 8-gram on the *full* anonymized brief collides for almost every pair. The pipeline therefore uses:

1. **Exact-input leak:** full anonymized input (brief + bench + thread + teaser) must not match across **train↔held-out**, **train↔dev**, or **dev↔held-out** pairs.
2. **High-entropy 8-grams:** 8-grams on `(company, domain, region, employees_bucket, public_context_teaser)` — held-out must not share an 8-gram with the **train** union or the **dev** union.
3. **Cheap embedding proxy:** **bag-of-word** cosine on that same slice (deterministic, no neural encoder); flag **held-out↔train** and **held-out↔dev** pairs with cosine **≥ 0.85** (see `thresholds.embedding_methodology` in the JSON for deviation vs. neural embeddings).
4. **Time-shift / signal-window:** if the brief or bench contains a four-digit **calendar year** (dated public signal), `internal_capacity_snapshot.as_of` must be present so capacity claims align to a documented snapshot window.

Latest run on v0.1 (240 tasks): **pass** — see JSON for `max_cosine_observed` per partition pair.

## 5) Inter-rater Agreement Protocol

- **Subset:** 30 tasks (six per failure dimension); **Pass 2 ≥24h after Pass 1** and **blind to Pass 1 labels** for human raters (`docs/inter_rater_human_protocol.md`).
- **Mechanical baseline:** Pass1 = `evaluation/scoring_evaluator.py` on the subset; Pass2 = identical re-score → **100%** agreement (proves determinism). Artifacts: `reports/inter_rater_agreement.md`, `reports/inter_rater/*`.
- **Human Pass2:** `python scripts/compute_inter_rater_agreement.py --human-pass2 <file.jsonl>`; per-dimension agreement matrix and **≥80%** target.
- **Benchmark rubric revision:** if any dimension &lt; 80%, log changes in `docs/rubric_revision_log.md` and re-score the **same 30** `task_id`s after edits to `scoring_evaluator.py` / methodology.

## 6) Automated coverage guarantees (Act II hardening)

These scripts close the gap between “catalogued intent” and “verified in the built corpus”:

| Script | Guarantee |
|--------|-----------|
| `scripts/verify_audit_probe_coverage.py` | Every `ADV-*` ID in `bench_corpus/audit_probe_registry.py` (from `docs/audit_memo.md`) appears on ≥1 scenario row; catalog probe IDs match the registry set. |
| `scripts/verify_scenario_catalog_integrity.py` | Every scenario has non-empty `edgecase_tags`, `audit_probes`, and complete `ground_truth` / template fields. |
| `scripts/verify_materialized_task_coverage.py` | Every materialized task carries `coverage` metadata, includes `internal_capacity_snapshot`, includes every audit probe somewhere in the 240 tasks, satisfies `grounding_anchors` on `candidate_output` when set, and self-scores ≥ pass threshold on `candidate_output`. |

Run them directly or via `python scripts/build_tenacious_bench_v01_package.py --run-checks`.

**Act III (Path B):** after `python scripts/build_path_b_preferences.py`, run `python scripts/verify_training_data_leakage.py` so `training_data/preferences.jsonl` stays train-partition-only and clear of dev/held high-entropy collisions (see `docs/methodology_rationale.md`).

**Not mechanically graded:** `edgecase_tags` beyond what maps into `scoring_evaluator.py` dimensions remain **documentation and analysis hooks** unless you extend the scorer or add task-local `ground_truth` flags.

## 7) Reproducibility and Cost Controls

- Fixed random seed in generation and dedup scripts.
- Logged model routing policy and judge thresholds in source + markdown.
- Eval-tier model restricted to calibration sample; cheap-tier models for bulk generation/filtering.
- **Judge audit log:** `python scripts/run_judge_filter_pipeline.py` writes `data/judge_filter_log.jsonl` (per-task 1–5 scores, thresholds, `decision`, `fail_reasons`, dev vs eval-tier judge id). `scripts/build_tenacious_bench_v01_package.py` runs this automatically before copying logs into `tenacious_bench_v0.1/generation_scripts/`.
- Cost ledger maintained under `reports/cost_log.md`.
