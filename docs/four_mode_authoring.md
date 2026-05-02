# Four-mode dataset authoring (Week 11 rubric map)

This note ties the **Four-Mode Dataset Authoring** criterion to **concrete files and fields** so reviewers do not have to hunt across the repo.

## Modes (must match `task["source_mode"]` and `schema.json`)

| Mode | What the code does | Where to look |
|------|---------------------|---------------|
| **trace_derived** | Binds Week 10 `(trace_id, lead_id)` from `bench_corpus.seeds.load_trace_anchors` into structured `authoring_metadata.trace_anchor` and `input_context.trace_anchor`, plus prose `provenance_note`. | `scripts/build_corpus.py`, `bench_corpus/scenarios.py`, `bench_corpus/seeds.py` |
| **programmatic** | Scenario template × combinatorial **company** slots (segment, region, `employees_bucket`, domain, teaser) × `bench_corpus.anchor_packs.build_anchor_ctx` (rotated funding/velocity/layoff/leadership lines + per-stack bench counts). Uses catalog rows with `authoring_kind=programmatic_template`. | `bench_corpus/scenarios.py`, `bench_corpus/anchor_packs.py`, `scripts/build_corpus.py` |
| **multi_llm_synthesis** | Same combinatorial shell as programmatic; **bulk author** model id from `generation.model_routing.pick_bulk_generator` is stored as `synthesis_route` (and duplicated in `authoring_metadata.synthesis_route_model_id`). | `generation/model_routing.py`, `scripts/build_corpus.py` |
| **hand_authored_adversarial** | Selects only catalog rows tagged `authoring_kind=hand_adversarial` (dual-source / override stress, multi-probe rows, and selected high-risk audit IDs — see `bench_corpus/authoring_modes.py`). | `bench_corpus/authoring_modes.py`, `bench_corpus/scenario_catalog.py` (post-load `tag_scenario_rows`) |

## Per-task metadata (visible on every built task)

- **`authoring_metadata`** (top-level on each task): `task_source_mode`, `catalog_authoring_kind`, `combinatorial_slots` (segment, region, headcount bucket, anchor rotation indices, bench stack counts, synthetic `ai_maturity_sweep_bucket` for methodology visibility), `trace_anchor`, `synthesis_route_model_id`, and **literal** `train_share_target_fractions` copied from constants for audit.
- **`coverage.source_mode`** and **`coverage.catalog_authoring_kind`**: duplicate the mode and template tier for quick grep.
- **`input_context.trace_anchor`**: structured trace ids when `source_mode=trace_derived`, else JSON `null`.

## Share targets (~30 / 30 / 25 / 15)

- **Declared floats:** `bench_corpus.constants.SOURCE_MODE_TRAIN_SHARE_TARGETS` (`trace_derived`, `programmatic`, `multi_llm_synthesis`, `hand_authored_adversarial`).
- **Integer realization:** `bench_corpus.constants.CELL_COUNTS` per `(failure_dimension, partition, source_mode)`.
- **Check:** `scripts/verify_composition.py` compares realized train marginals to targets.

## Combinatorial population

Slots are populated at `build_task_payload` time from each company seed row and the optional bench snapshot, then recorded under `authoring_metadata.combinatorial_slots`. Anchor line choice is deterministic in `anchor_packs.anchor_rotation_indices(seq)` (aligned with `build_anchor_ctx`).
