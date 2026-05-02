# Path B training data (`preferences.jsonl`)

Act III deliverable for **preference optimization** (DPO / SimPO / ORPO): teach a small critic to prefer **chosen** email drafts over **rejected** ones for the same Tenacious context.

## Regenerate

From repo root (`tenacious-bench/`):

```bash
python scripts/build_path_b_preferences.py
# optional: --max-pairs-per-task N --mutators weak_hard_assert,bench_risky_phrase --dry-run
python scripts/verify_training_data_leakage.py
```

## Schema (one JSON object per line)

| Field | Description |
|-------|-------------|
| `prompt` | Deterministic critic context from [`bench_corpus/critic_prompt.py`](../bench_corpus/critic_prompt.py) — **no** candidate email. |
| `chosen` | Reference email (`Subject:` + body). Must pass `score_task(task, chosen)` at `pass_threshold`. |
| `rejected` | Synthetic policy violation; must **fail** `score_task` globally (after `finalize_rejected_below_threshold`) and fail the target dimension (score ≤1). |
| `source_task_id` | `tb_v01_*` from `data/tasks_train.jsonl` only. |
| `failure_dimension` | Bench failure dimension. |
| `source_mode` | trace_derived / programmatic / multi_llm_synthesis / hand_authored_adversarial |
| `edgecase_tags` | From task `coverage`. |
| `audit_probes` | From task `coverage`. |
| `chosen_source` | Always `benchmark_candidate` unless you add OpenRouter rewrites. |
| `rejected_mutator_id` | e.g. `weak_hard_assert`, `tone_banned_world_class`. |
| `target_violation_dimension` | Rubric dimension the mutator is verified to break. |
| `evaluator_pass_chosen` | Always `true` for built rows (re-verified by `verify_training_data_leakage.py`). |
| `evaluator_pass_rejected` | Always `false` (rejected must not pass `pass_threshold`). |
| `evaluator_total_score_chosen` / `evaluator_total_score_rejected` | Totals at build time for quick QA. |
| `evaluator_scores_chosen` | Map `dimension_name -> score` for audit. |
| `evaluator_scores_rejected` | Same for rejected. |
| `pass_threshold` | Copied from source task. |
| `schema_version` | e.g. `1.1` |

## Golden row shape (abbreviated)

```json
{
  "prompt": "## Task\\ntask_id: tb_v01_000001\\n...\\n## Internal_capacity_snapshot_json\\n{...}\\n",
  "chosen": "Subject: Question: ...\\n\\nHello,\\n\\n...",
  "rejected": "Subject: Question: ...\\n\\nHello,\\n\\n...You are clearly scaling fast...",
  "source_task_id": "tb_v01_000001",
  "failure_dimension": "weak_signal_calibration",
  "chosen_source": "benchmark_candidate",
  "rejected_mutator_id": "weak_hard_assert",
  "target_violation_dimension": "confidence_calibration"
}
```

## Policies

- **Train partition only:** pairs are built exclusively from `data/tasks_train.jsonl`.
- **Preference leakage:** if you add LLM rewrites for `chosen`, use a **different model family** than the judge on the same example (see `docs/methodology.md`, Li et al.).
- **Act IV:** load `preferences.jsonl` into HuggingFace `datasets` and apply the Qwen 3.5 + Unsloth recipe from the Week 11 Production Stack.
