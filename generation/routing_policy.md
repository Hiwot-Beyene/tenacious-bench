# Multi-LLM Routing Policy (v0.1)

## Objective
Prevent **preference leakage** (Li et al., 2025, arXiv:2502.01534) while producing diverse, verifiable Tenacious-Bench tasks.

## Role assignment (named model ids)
Canonical constants live in `generation/model_routing.py`.

| Role | Model id(s) | API / configuration |
|------|-------------|---------------------|
| **Frontier seed author** (rare) | `anthropic/claude-sonnet-4.6` | OpenRouter or direct API; **not** invoked in deterministic v0.1 corpus build |
| **Dev-tier bulk generator** | `qwen/qwen3-next-80b-a3b-instruct`, `deepseek/deepseek-chat` | OpenRouter `POST /api/v1/chat/completions` when extending synthesis beyond templates |
| **Dev-tier judge** (bulk filter) | Paired automatically: **never the same id** as the task’s bulk generator | Deterministic mechanical judge in `generation/pointwise_judge.py` by default; optional `generation/openrouter_judge.py` when `OPENROUTER_API_KEY` is set |
| **Eval-tier judge** (calibration only) | `openai/gpt-5` | Reserved for **≤50** dev+heldout spot-checks per `scripts/run_judge_filter_pipeline.py`; bulk rows must not use this id |

**Catalog-authored tasks** (trace/programmatic/hand modes): author stub is `deterministic/v0.1-scenario-catalog`; dev-tier judge is the first cheap-tier id in `model_routing.py` (distinct string from the stub).

## Rotation rule
For each **multi-LLM synthesis** task:
1. Pick bulk generator by deterministic round-robin (`pick_bulk_generator(seq)` in `scripts/build_corpus.py`).
2. Pick dev-tier judge with `dev_judge_for_bulk_generator(generator)` — **must differ** from the generator model id.
3. Reject any pipeline configuration where `generator_model == judge_model`.

## Family separation
Judge filter models must **not** reuse the same OpenRouter model id as the bulk generator for that task. Eval-tier calibration uses a **third** id (`openai/gpt-5`) on the fixed calibration subset only.

## Judge filter dimensions
Pointwise scoring (1–5), prompt: `prompts/judge_pointwise.md`. Dimensions:
- `input_coherence`
- `ground_truth_verifiability`
- `rubric_application_clarity`

**Inclusion thresholds** (see `generation/judge_filter.py`): each dimension **≥ 4**.

## Pairwise dedup
Near-duplicates: `generation/dedup_pairwise.py`. Keep the candidate with higher:
1. `rubric_application_clarity`
2. `ground_truth_verifiability`
3. length of `candidate_output`

## Eval-tier budget guard
Eval-tier judge id applies to **at most 50** tasks (dev+heldout sample). All other rows use dev-tier judge pairing.

## Reproducibility
Corpus slotting seed defaults to `11711` (documented in package `seed_counts.json`). Judge audit log: `python scripts/run_judge_filter_pipeline.py` → `data/judge_filter_log.jsonl`.
