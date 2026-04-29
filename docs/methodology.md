# Methodology (Interim): Tenacious-Bench v0.1

## 1) Declared Training Path

**Path B — Preference-tuned judge/critic**.

Why Path B (not A/C) from Week 10 evidence:
- Week 10 shows repeated cases where pipeline execution succeeded while policy-safe sales behavior still required stricter filtering. Example traces: `3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95`, `85724927-681b-47b5-ba65-a13d705084c6`, `0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac`.
- This is a **consistency/decision-quality** profile, not only a text-generation profile. The required intervention is a critic that can reject unsafe outputs (over-assertion, over-commitment, condescension) even when language quality is high.
- Path B best matches that profile and is cheaper/faster to harden for interim deliverables.

## 2) Reading-Informed Design Choices

We anchor the design to required reading:
- **Gu et al. (LLM-as-a-Judge Survey)**: we decompose scoring into mechanically checkable dimensions plus bounded judge components; we do not rely on a single opaque score.
- **Li et al. (Preference Leakage)**: generation and judging must rotate model families so the same model does not author and judge the same example.
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
- **Dev 30%**: public, used for rubric/debug iteration.
- **Held-out 20%**: sealed for final reporting.

Stratification logic:
- Primary strata are Week 10 failure dimensions from `probes/failure_taxonomy.md` (ICP integrity, signal reliability, bench alignment, tone/brand safety, coordination, pricing/cost, scheduling/global logistics, competitive-gap rigor, stakeholder engagement).
- Each partition preserves category distribution so no single split over-represents one failure type.
- Within category, source-mode quotas are tracked: trace-derived, programmatic sweep, multi-LLM synthesis, hand-authored adversarial.

## 4) Contamination Checks (Interim Pilot Results)

Interim pilot run was executed on a proto pool (n=36 candidate tasks; train/dev/held-out draft split only).

### n-gram overlap check
- Rule: reject held-out examples with >=8-gram overlap against train.
- Flags: **4** candidate pairs.
- Resolution: **2 rewritten**, **2 dropped**.

### embedding similarity check
- Rule: cosine similarity >0.85 between held-out and train is flagged.
- Flags: **3** candidate pairs.
- Resolution: **1 kept with justification** (same domain entities, different scoring target), **2 dropped**.

### time-shift verification
- Rule: tasks with dated public-signal claims must map to documented windows.
- Flags: **2** candidates (ambiguous event time references).
- Resolution: **2 rewritten** with explicit time anchors.

Final pilot pass status: **PASS** for provisional held-out slice after rewrite/drop actions.

## 5) Inter-rater Agreement Protocol

- Label 30 tasks with full rubric.
- Re-label same 30 tasks after 24h blind to first labels.
- Threshold: >=80% agreement per dimension.
- If any dimension <80%, revise rubric definitions and re-label the same set.
- Interim status: protocol defined; full agreement matrix to be committed in `reports/inter_rater_agreement.md` after first complete 30-task pass.

## 6) Reproducibility and Cost Controls

- Fixed random seed in generation and dedup scripts.
- Logged model routing policy and judge thresholds in source + markdown.
- Eval-tier model restricted to calibration sample; cheap-tier models for bulk generation/filtering.
- Cost ledger maintained under `reports/cost_log.md`.
