# Multi-LLM Routing Policy (Interim v0.1)

## Objective
Prevent preference leakage while producing diverse, verifiable Tenacious-Bench tasks.

## Model Families
- **Cheap-tier generation (bulk):** `qwen/qwen3-next-80b-a3b-instruct`, `deepseek/deepseek-chat`.
- **Eval-tier calibration only (small sample):** `anthropic/claude-sonnet-4.6`, `openai/gpt-5` (or configured equivalent).
- **Judge model family:** must differ from generator family for each example.

## Rotation Rule
For each generated task:
1. Select generator family by deterministic round-robin over cheap-tier list.
2. Select judge family from a different family than the generator.
3. Reject any example where `generator_model == judge_model` or same family.

## Judge Filter Dimensions
Pointwise judge scoring (1-5) on:
- input coherence
- ground-truth verifiability
- rubric-application clarity

Inclusion thresholds (interim):
- coherence >= 4
- verifiability >= 4
- rubric clarity >= 4

## Pairwise Dedup Selection
When near-duplicate candidates are detected, keep the candidate with:
1. higher rubric-clarity score
2. then higher verifiability
3. then longer rationale coverage

## Eval-Tier Budget Guard
Eval-tier calls are limited to calibration sample only (target <= 50 tasks). Bulk generation/filtering is cheap-tier only.

## Reproducibility
All scripts accept and persist a reproducibility seed (`--seed`, default `11711`).
