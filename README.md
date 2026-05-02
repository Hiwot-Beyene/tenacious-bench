# Tenacious-Bench v0.1

**Author:** [Hiwot Beyene](https://huggingface.co/hiwot-beyene) · **Source:** [github.com/Hiwot-Beyene/tenacious-bench](https://github.com/Hiwot-Beyene/tenacious-bench)

Tenacious-Bench is a sales-agent **evaluation** harness and domain dataset for the Tenacious B2B outreach workflow. It targets what generic benchmarks under-grade: **weak-signal calibration**, **bench/capacity honesty**, **tone-marker compliance**, **CRM/human override obedience**, and **non-condescending gap framing**. This repo is my Week 11 TRP1 deliverable: **Path B** preference tuning (DPO + LoRA critic), public **Hugging Face** artifacts, **blog**, **community** presence, **`memo.pdf`**, and **`evidence_graph.json`**.

---

## Status

| Phase | State |
|-------|--------|
| Acts I–II | Audit, schema, ~240 tasks, partitions, datasheet, contamination + inter-rater |
| Act III | Path B `preferences.jsonl` + leakage QA |
| Act IV | TRL `DPOTrainer` + LoRA; sealed ablation harness; `reports/model_card.md` |
| Act V | HF dataset + adapter published; Substack blog; HF discussions; CEO/CFO memo PDF |

**Declared path:** **B** — preference-tuned judge/critic (see [`docs/methodology.md`](docs/methodology.md)).

---

## Public artifacts (URLs)

These satisfy the Week 11 **final submission** public-URL checklist and are mirrored in [`reports/act_v_urls.json`](reports/act_v_urls.json).

| Artifact | URL |
|----------|-----|
| **Hugging Face dataset** | [https://huggingface.co/datasets/hiwot-beyene/tenacious-bench-v0.1](https://huggingface.co/datasets/hiwot-beyene/tenacious-bench-v0.1) |
| **Hugging Face model (Path B LoRA adapter)** | [https://huggingface.co/hiwot-beyene/tenacious-bench-lora](https://huggingface.co/hiwot-beyene/tenacious-bench-lora) |
| **Technical blog post** (1,200–2,000 words) | [https://hiwotbeyene.substack.com/p/what-style-benches-miss-about-b2b](https://hiwotbeyene.substack.com/p/what-style-benches-miss-about-b2b) |
| **Community engagement** | [Hugging Face dataset discussions](https://huggingface.co/datasets/hiwot-beyene/tenacious-bench-v0.1/discussions) (public community tab). Optional cross-post: [τ²-Bench issues](https://github.com/sierra-research/tau2-bench/issues) — template in [`docs/act_v_publish_and_community_guide.md`](docs/act_v_publish_and_community_guide.md). |
| **CEO/CFO memo** | **`memo.pdf`** at repo root — generate: `uv sync --extra pdf && uv run python scripts/generate_memo_pdf.py` |
| **Evidence graph** | [`reports/evidence_graph.json`](reports/evidence_graph.json) — run `uv run python scripts/emit_evidence_graph.py` after editing `act_v_urls.json` |

Hub model card (generated): [hiwot-beyene/tenacious-bench-lora](https://huggingface.co/hiwot-beyene/tenacious-bench-lora) — align YAML metadata in the Hub UI if you see a metadata warning.

---

## Quickstart: reproduce a headline number (< 1 hour)

The challenge asks for a **quickstart a stranger can run** to hit a **headline** metric. Two tiers:

### A) Mechanical scorer only (CPU, ~5 minutes)

No ML stack required beyond Python 3.11+.

```bash
git clone https://github.com/Hiwot-Beyene/tenacious-bench.git
cd tenacious-bench
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python evaluation/scoring_evaluator.py evaluation/tasks_examples/weak_signal_ask_vs_assert.json
```

You should see **deterministic JSON scores** for the fixture task (rubric dimensions + pass/fail). This exercises the same `scoring_evaluator.py` used across the 240-task corpus.

### B) Path B held-out Delta A (GPU recommended, ~30–90 min with deps + weights)

Reproduces the **paired bootstrap Delta A** (trained vs baseline) reported on the [model card](https://huggingface.co/hiwot-beyene/tenacious-bench-lora) when `reports/ablation_results.json` matches a full sealed run.

```bash
cd tenacious-bench
uv sync --extra train
uv run python scripts/build_heldout_eval_pairs.py
uv run python scripts/run_sealed_ablation.py --adapter outputs/preference_lora_day5/lora_adapter
```

Inspect `reports/ablation_results.json` → `delta_a_trained_vs_baseline`. To align with the **published adapter**, download it from Hugging Face and pass `--adapter /path/to/lora_adapter`.

---

## Setup & dependency pinning

| Mechanism | Purpose |
|-----------|---------|
| [`pyproject.toml`](pyproject.toml) | Project metadata + optional extras: `train`, `pdf`, `publish` |
| [`uv.lock`](uv.lock) | **Locked** dependency versions (primary reproducibility surface for `uv`) |
| [`requirements.txt`](requirements.txt) | **Pip** install with hashed pins — run `uv export` to refresh (see file header) |

**Recommended install (full Act IV–V):**

```bash
cd tenacious-bench
uv sync --extra train --extra pdf --extra publish
```

**Python:** 3.11+

---

## License

This repository is released under **CC-BY-4.0** — see [`LICENSE`](LICENSE). The published Hugging Face dataset card should stay consistent with that choice (see [`publication/hf_dataset/README.md`](publication/hf_dataset/README.md)).

---

## Attribution & credits

- **Author / maintainer:** Hiwot Beyene — Week 11 Tenacious-Bench submission.
- **Workflow domain** “Tenacious” is used as an **evaluation** and engineering context only; no proprietary customer content is published here.
- **Ideas & citations** (synthesis memos and methodology): Liu et al. (synthetic data); Gebru et al., Pushkarna et al. (dataset documentation); Chen et al. (contamination); Gu et al. (LLM-as-judge); Rafailov et al., Meng et al., Hong et al. (preference optimization); Li et al. (preference leakage); and related Path B references in [`docs/methodology_rationale.md`](docs/methodology_rationale.md) and [`synthesis_memos/`](synthesis_memos/).
- **Software stack:** [PyTorch](https://pytorch.org/), [Hugging Face Transformers / TRL / PEFT / Datasets](https://huggingface.co/docs), base LM [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) for the shipped adapter run.
- **Contrast benchmark:** [τ²-Bench / τ-Bench](https://github.com/sierra-research/tau2-bench) (tool–user–agent retail-style trajectories). Tenacious-Bench targets **B2B outbound policy** dimensions; see [`docs/audit_memo.md`](docs/audit_memo.md).

---

## Act V maintenance commands

```bash
uv run python scripts/emit_evidence_graph.py
uv run python scripts/verify_act_v_deliverables.py --strict-urls --require-evidence-graph --require-community-url
```

---

## Current status (deliverables detail)

### Completed (robust core)

- Audit memo: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology + Path B rationale: [`docs/methodology.md`](docs/methodology.md), [`docs/methodology_rationale.md`](docs/methodology_rationale.md)
- Mechanical scorer: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Examples + schema: [`evaluation/tasks_examples/`](evaluation/tasks_examples/), [`schema.json`](schema.json)
- Datasheet: [`docs/datasheet.md`](docs/datasheet.md)
- **Act II package** generator: [`scripts/build_tenacious_bench_v01_package.py`](scripts/build_tenacious_bench_v01_package.py) → [`tenacious_bench_v0.1/README.md`](tenacious_bench_v0.1/README.md)
- **Corpus:** [`data/tasks_all.jsonl`](data/tasks_all.jsonl), [`data/company_seeds.json`](data/company_seeds.json), [`scripts/build_corpus.py`](scripts/build_corpus.py); **four-mode authoring map:** [`docs/four_mode_authoring.md`](docs/four_mode_authoring.md)
- Contamination: [`reports/contamination_check.json`](reports/contamination_check.json)
- Inter-rater: [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md)
- Synthesis memos: [`synthesis_memos/`](synthesis_memos/)

### Act III — Path B training data

- [`training_data/preferences.jsonl`](training_data/preferences.jsonl), [`training_data/manifest.json`](training_data/manifest.json)
- [`scripts/build_path_b_preferences.py`](scripts/build_path_b_preferences.py), [`scripts/verify_training_data_leakage.py`](scripts/verify_training_data_leakage.py)

### Act IV — Train + ablate

- [`training/preference_lora_train.py`](training/preference_lora_train.py)
- [`scripts/export_unsloth_splits.py`](scripts/export_unsloth_splits.py), [`scripts/build_heldout_eval_pairs.py`](scripts/build_heldout_eval_pairs.py), [`scripts/run_sealed_ablation.py`](scripts/run_sealed_ablation.py)
- [`scripts/emit_model_card.py`](scripts/emit_model_card.py) → [`reports/model_card.md`](reports/model_card.md)

### Act V — Publish kit

| Deliverable | Location |
|-------------|----------|
| URL ledger | [`reports/act_v_urls.json`](reports/act_v_urls.json) |
| Evidence graph | [`scripts/emit_evidence_graph.py`](scripts/emit_evidence_graph.py) |
| Verification | [`scripts/verify_act_v_deliverables.py`](scripts/verify_act_v_deliverables.py) |
| Hub upload helper | [`scripts/hf_act_v_upload_helper.py`](scripts/hf_act_v_upload_helper.py) |
| Blog source | [`docs/act_v_blog_post.md`](docs/act_v_blog_post.md) |
| Publish guide | [`docs/act_v_publish_and_community_guide.md`](docs/act_v_publish_and_community_guide.md) |

---

## Challenge requirement mapping (reviewer fast path)

| Requirement | Artifact(s) |
|-------------|-------------|
| Audit + Week 10 evidence | [`docs/audit_memo.md`](docs/audit_memo.md) |
| Scoring evaluator | [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py) |
| Corpus + scenarios | [`scripts/build_corpus.py`](scripts/build_corpus.py), [`bench_corpus/`](bench_corpus/) |
| Datasheet | [`docs/datasheet.md`](docs/datasheet.md) |
| Methodology | [`docs/methodology.md`](docs/methodology.md) |
| Composition / inter-rater / contamination | [`reports/composition_crosstab.md`](reports/composition_crosstab.md), [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md), [`reports/contamination_check.json`](reports/contamination_check.json) |
| Act III Path B | [`training_data/`](training_data/), [`scripts/verify_training_data_leakage.py`](scripts/verify_training_data_leakage.py) |
| Act IV | [`training/preference_lora_train.py`](training/preference_lora_train.py), [`scripts/run_sealed_ablation.py`](scripts/run_sealed_ablation.py), [`reports/training_run.log`](reports/training_run.log), [`reports/ablation_results.json`](reports/ablation_results.json) |
| Act V | **Public URLs above**, [`reports/evidence_graph.json`](reports/evidence_graph.json), **`memo.pdf`**, this README |

**Suggested 10-minute review:** README → `docs/audit_memo.md` → `evaluation/scoring_evaluator.py` + one example task → `docs/datasheet.md` → HF dataset + model card links.

---

## Build corpus, QA, and Act II package

```bash
python scripts/build_corpus.py              # optional: --refresh-seeds
python scripts/run_judge_filter_pipeline.py
python scripts/run_contamination_check.py
python scripts/verify_composition.py
python scripts/verify_audit_probe_coverage.py
python scripts/verify_scenario_catalog_integrity.py
python scripts/verify_materialized_task_coverage.py
python scripts/compute_inter_rater_agreement.py
python scripts/build_tenacious_bench_v01_package.py --run-checks
```

---

## Run the scoring evaluator (batch)

```bash
python evaluation/scoring_evaluator.py evaluation/tasks_examples/weak_signal_ask_vs_assert.json
python evaluation/scoring_evaluator.py evaluation/tasks_examples/*.json
```

---

## Repository structure

- `docs/` — audit, methodology, datasheet, Act V writeups
- `data/` — materialized task JSONL + `company_seeds.json`
- `training_data/` — Path B preferences + manifest
- `evaluation/` — scorer + fixtures
- `bench_corpus/` — scenarios, constants, critic helpers
- `generation/` — judge filter, contamination, dedup
- `training/` — `preference_lora_train.py`
- `scripts/` — build, verify, Act II package, HF helpers, `generate_memo_pdf.py`
- `reports/` — logs, ablation, `model_card.md`, `act_v_urls.json`, `evidence_graph.json`
- `publication/` — Hub README templates
- `synthesis_memos/` — paper memos

---

## Major links

- Layman guide: [`docs/Conversion_Engine_and_Tenacious_Bench_Explained.md`](docs/Conversion_Engine_and_Tenacious_Bench_Explained.md)
- Week 11 brief (local): [`TRP1 Challenge Week 11_ Sales Agent Evaluation Bench.md`](TRP1%20Challenge%20Week%2011_%20Sales%20Agent%20Evaluation%20Bench.md)
- Sample scores: [`reports/sample_scores.jsonl`](reports/sample_scores.jsonl)
- Cost log: [`reports/cost_log.md`](reports/cost_log.md)

---

## Post–Week 11

1. More preference pairs / SimPO–ORPO experiments if Delta A is underpowered.
2. Optional Zenodo DOI; keep Hub `revision` pins.
3. Production A/B on real pipelines—bench metrics are necessary, not sufficient.
