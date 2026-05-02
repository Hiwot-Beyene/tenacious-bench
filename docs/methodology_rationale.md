# Methodology rationale — Path B (Act III)

## Explicit path choice

**Path B (preference-tuned critic / judge)** is declared in `docs/methodology.md`. We do **not** pursue Path A (SFT on generations) or Path C (process / trajectory reward) as the primary Week 11 training path.

## Week 10 trace evidence (failure pattern)

Week 10 traces show **fluent execution with policy-unsafe decisions**: weak-signal over-assertion, bench misalignment, tone/brand risk, and override-adjacent behavior. Representative trace IDs (public log anchors for the audit):

- `3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95`
- `85724927-681b-47b5-ba65-a13d705084c6`
- `0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac`

These support **inconsistency / accept–reject** failure: the stack can **produce** polished text while still **failing** business gates that require rejecting or softening the draft.

## Failure-mode mapping: why Path B (not A or C)

| Path | Target failure mode | Fit to Week 10 evidence |
|------|---------------------|---------------------------|
| **A — SFT / generation quality** | Wording, fluency, style | **Dismissed as primary:** our worst errors are **decision errors** (when to assert, what to promise, tone under weak signal), not raw generation quality alone. SFT risks overfitting phrasing without a **rejection signal**. |
| **B — Preference / critic tuning** | **Inconsistency:** model does not reliably prefer policy-safe vs unsafe completions | **Chosen:** matches traces where outputs look acceptable but violate calibration, bench honesty, or coordination norms. A critic aligns with **binary / ranking** supervision on the same context. |
| **C — Process / trajectory reward** | Long-horizon **trajectory** quality (tool chains, CRM state) | **Deferred:** valuable for full Conversion Engine loops, but higher implementation cost for Week 11; v0.1 tasks are **single-turn email** graded objects. Path C is documented as v0.2+ if JSON state or traces are added. |

## Algorithm choice: SimPO (reference-free preference optimization)

We adopt **SimPO** (Meng et al., NeurIPS 2024) for the first training run: the paper’s **§3–4** develop a **reference-free** objective (length-normalized implicit reward), which fits the Week 11 compute envelope when hosting a frozen reference logit pipeline beside the adapter is awkward.

**DPO** (Rafailov et al., NeurIPS 2023) remains the conceptual baseline: **§3** derives the Bradley–Terry preference likelihood and the closed-form preference loss; we cite it for reviewers who expect the classical derivation.

**ORPO** (Hong et al., EMNLP 2024) remains a documented fallback if SimPO is unstable on small **N** (see paper’s combined odds-ratio formulation in the empirical sections).

## Read papers — specific sections / claims used here

1. **Li et al. (2025), *Preference Leakage* (arXiv:2502.01534):** **§2–3** define leakage when the **same model family** generates and judges preferences, inflating offline alignment metrics. **Control:** rotated generator vs judge families in `generation/model_routing.py`; Path B `chosen` is benchmark `candidate_output` + deterministic `rejected` arms (`training_data/README.md`).
2. **Gu et al., LLM-as-a-Judge survey:** **§5–6** (bias / decomposition): we keep a **decomposed** Tenacious-Bench mechanical rubric (grounding, calibration, tone, bench, format) as the training labeler rather than a single scalar LLM score.
3. **Rafailov et al., DPO (NeurIPS 2023):** **§3** — preference modeling objective; baseline for understanding SimPO as a reference-free variant.
4. **Meng et al., SimPO (NeurIPS 2024):** **§3–4** — SimPO loss and empirical gains without a reference model.

*(Section numbers refer to the published PDF / arXiv structure; use the authoritative PDF if pagination differs.)*

## Data construction (Act III)

- **Source:** `data/tasks_train.jsonl` only → `training_data/preferences.jsonl`.
- **Prompt:** `bench_corpus.critic_prompt.build_critic_prompt` — no reference email in the prompt.
- **Chosen:** passes `evaluation/scoring_evaluator.score_task` at `pass_threshold`.
- **Rejected:** `bench_corpus.preference_mutators` + global fail gate; verified in `scripts/build_path_b_preferences.py` and `scripts/verify_training_data_leakage.py`.
- **Leakage philosophy:** mirrors `generation/contamination_check.py` (high-entropy slice, cosine bound **0.85**, train-only IDs).

## Limitations

The critic sees **single-turn email** prompts; multi-turn CRM state is partially text-only. Extending to Path C-style **trajectory** critics would require structured state blocks or trace-conditioned rewards in a future version.
