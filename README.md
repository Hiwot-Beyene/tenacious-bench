# Tenacious-Bench

Tenacious-Bench is a sales-agent evaluation bench for the Tenacious workflow domain. It targets behaviors that public benchmarks under-grade in B2B outreach: confidence calibration under weak signals, bench commitment safety, tone-marker compliance, coordination with CRM overrides, and non-condescending gap framing.

## Current Status (Week 11 — Act II pipeline)

### Completed (robust core)
- Audit memo with Week 10 evidence links: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology rationale (Path B): [`docs/methodology.md`](docs/methodology.md)
- Mechanical scoring evaluator: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Example tasks (incl. adversarial fail fixture): [`evaluation/tasks_examples/`](evaluation/tasks_examples/)
- Formal task schema: [`schema.json`](schema.json)
- Datasheet draft with Gebru + Pushkarna layers: [`docs/datasheet.md`](docs/datasheet.md)
- **Act II deliverable folder** [`tenacious_bench_v0.1/`](tenacious_bench_v0.1/) — **generated** by [`scripts/build_tenacious_bench_v01_package.py`](scripts/build_tenacious_bench_v01_package.py) (use `--run-checks` to run contamination + composition + inter-rater first). Only [`tenacious_bench_v0.1/README.md`](tenacious_bench_v0.1/README.md) is tracked; shards and copied reports are gitignored to avoid duplicating `data/` and `reports/`.
- **v0.1 corpus (240 tasks)** from **real company seeds** (Crunchbase ODM + Conversion Engine workspaces in [`data/company_seeds.json`](data/company_seeds.json)) and **expanded scenario catalog** [`bench_corpus/scenario_catalog.py`](bench_corpus/scenario_catalog.py) (ICP segments 1–4, AI-maturity / Segment-4 gating, layoffs.fyi + enrichment tool failures, HubSpot/sequence/CRM, Langfuse, email-vs-SMS, bench/MSA/DPA/pricing gates, audit probes ADV-\* from [`docs/audit_memo.md`](docs/audit_memo.md)). Each task carries `coverage.edgecase_tags` + `audit_probes`. Builder: [`scripts/build_corpus.py`](scripts/build_corpus.py); composition: [`scripts/verify_composition.py`](scripts/verify_composition.py). [`scripts/materialize_corpus.py`](scripts/materialize_corpus.py) shims to `build_corpus.py`.
- **Inter-rater agreement (n=30)**: [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md), [`reports/inter_rater/`](reports/inter_rater/), [`scripts/compute_inter_rater_agreement.py`](scripts/compute_inter_rater_agreement.py)
- Generation pipeline scaffolds + routing policy: [`generation/`](generation/), [`generation/routing_policy.md`](generation/routing_policy.md)
- Judge prompts committed as text: [`prompts/`](prompts/)
- **Four common-reading synthesis memos** (critical engagement):
  - [`synthesis_memos/memo_liu_2024_synthetic_data.md`](synthesis_memos/memo_liu_2024_synthetic_data.md)
  - [`synthesis_memos/memo_gu_llm_as_judge.md`](synthesis_memos/memo_gu_llm_as_judge.md)
  - [`synthesis_memos/memo_gebru_pushkarna_documentation.md`](synthesis_memos/memo_gebru_pushkarna_documentation.md)
  - [`synthesis_memos/memo_chen_emnlp2025_contamination.md`](synthesis_memos/memo_chen_emnlp2025_contamination.md)
- **Contamination pipeline:** [`generation/contamination_check.py`](generation/contamination_check.py) — run [`scripts/run_contamination_check.py`](scripts/run_contamination_check.py) → [`reports/contamination_check.json`](reports/contamination_check.json)
- **Inter-rater:** [`scripts/compute_inter_rater_agreement.py`](scripts/compute_inter_rater_agreement.py); optional human Pass2 — [`docs/inter_rater_human_protocol.md`](docs/inter_rater_human_protocol.md)

### In progress (Acts III–V)
- Path B training run + HuggingFace dataset/model cards
- Public blog + community engagement artifact

## Challenge Requirement Mapping (Reviewer Fast Path)

This section maps each Week 11 interim requirement directly to committed artifacts so the repo can be graded without searching.

| Challenge requirement | Primary artifact(s) |
|---|---|
| Audit memo with Week 10 evidence | [`docs/audit_memo.md`](docs/audit_memo.md) |
| Scoring evaluator with mechanical decomposition + error handling | [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py), [`evaluation/tasks_examples/`](evaluation/tasks_examples/) |
| Corpus builder + scenarios | [`scripts/build_corpus.py`](scripts/build_corpus.py), [`bench_corpus/`](bench_corpus/) (seeds, scenarios, constants) |
| Optional LLM synthesis / routing / judge filter | [`generation/generate_tasks.py`](generation/generate_tasks.py) (optional), [`generation/judge_filter.py`](generation/judge_filter.py), [`generation/dedup_pairwise.py`](generation/dedup_pairwise.py), [`generation/contamination_check.py`](generation/contamination_check.py), [`generation/routing_policy.md`](generation/routing_policy.md) |
| Datasheet (Gebru + Pushkarna layers) | [`docs/datasheet.md`](docs/datasheet.md) |
| Methodology rationale (Path B + citations + contamination protocol) | [`docs/methodology.md`](docs/methodology.md) |
| Synthesis memos with critical engagement (4 common) | [`synthesis_memos/`](synthesis_memos/) — Liu, Gu, Gebru/Pushkarna, Chen |
| Composition + inter-rater + contamination | [`reports/composition_crosstab.md`](reports/composition_crosstab.md), [`reports/composition_actual.json`](reports/composition_actual.json), [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md), [`reports/inter_rater/`](reports/inter_rater/), [`reports/sample_scores.jsonl`](reports/sample_scores.jsonl), [`reports/contamination_check.json`](reports/contamination_check.json) |
| `tenacious_bench_v0.1/` (partitions + datasheet + contamination + inter-rater + generation_scripts) | [`tenacious_bench_v0.1/`](tenacious_bench_v0.1/), [`scripts/build_tenacious_bench_v01_package.py`](scripts/build_tenacious_bench_v01_package.py) |
| Materialized dataset + scripts | [`data/tasks_all.jsonl`](data/tasks_all.jsonl), [`data/company_seeds.json`](data/company_seeds.json), [`scripts/build_corpus.py`](scripts/build_corpus.py), [`scripts/verify_composition.py`](scripts/verify_composition.py), [`scripts/compute_inter_rater_agreement.py`](scripts/compute_inter_rater_agreement.py) |
| Audit probe + catalog + materialized QA | [`bench_corpus/audit_probe_registry.py`](bench_corpus/audit_probe_registry.py), [`scripts/verify_audit_probe_coverage.py`](scripts/verify_audit_probe_coverage.py), [`scripts/verify_scenario_catalog_integrity.py`](scripts/verify_scenario_catalog_integrity.py), [`scripts/verify_materialized_task_coverage.py`](scripts/verify_materialized_task_coverage.py) |

Suggested review order (10-minute pass):
1. `README.md` (this file)
2. `docs/audit_memo.md` and `docs/methodology.md`
3. `evaluation/scoring_evaluator.py` and `evaluation/tasks_examples/*.json`
4. `docs/datasheet.md`
5. `data/tasks_all.jsonl` + `reports/composition_crosstab.md`
6. `reports/inter_rater_agreement.md` + `reports/contamination_check.json`

## Build corpus, QA, and Act II package

```bash
python scripts/build_corpus.py              # optional: --refresh-seeds to rebuild company_seeds.json
python scripts/run_contamination_check.py
python scripts/verify_composition.py
python scripts/verify_audit_probe_coverage.py
python scripts/verify_scenario_catalog_integrity.py
python scripts/verify_materialized_task_coverage.py
python scripts/compute_inter_rater_agreement.py
python scripts/build_tenacious_bench_v01_package.py --run-checks   # optional: also pass --rebuild-corpus
```

`--run-checks` re-runs contamination, composition, and inter-rater before copying shards into `tenacious_bench_v0.1/`.

## Environment Setup

### Requirements
- Python **3.11+**
- Standard library is sufficient for interim evaluator scripts
- Optional for future pipeline runs: `httpx`, `numpy`, `pandas`, `sentence-transformers`

### Install
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## Run the Scoring Evaluator

Score one sample task:
```bash
python evaluation/scoring_evaluator.py evaluation/tasks_examples/weak_signal_ask_vs_assert.json
```

Score all current examples:
```bash
python evaluation/scoring_evaluator.py evaluation/tasks_examples/*.json
```

## Repository Structure

- `docs/` - audit memo, methodology, datasheet
- `tenacious_bench_v0.1/` - **generated** Act II layout (see `tenacious_bench_v0.1/README.md`; tracked outputs gitignored)
- `data/` - `company_seeds.json`, materialized task JSONL (train/dev/heldout/all)
- `bench_corpus/` - seed loader, scenario library, rubric constants (single source for task text)
- `scripts/` - corpus build, contamination CLI, composition verification, inter-rater tooling, Act II package assembler
- `evaluation/` - scoring evaluator and example tasks
- `schema.json` - canonical task object contract for examples and generated tasks
- `generation/` - synthesis, judge filter, dedup, contamination scaffolds
- `prompts/` - judge prompt text files (pointwise + pairwise)
- `reports/` - run reports (contamination, scoring outputs, cost logs)
- `synthesis_memos/` - paper memos with evidence-backed disagreements

## Major Artifact Links

- **Layman guide (Conversion Engine data + Tenacious-Bench tasks):** [`docs/Conversion_Engine_and_Tenacious_Bench_Explained.md`](docs/Conversion_Engine_and_Tenacious_Bench_Explained.md)
- Week 11 challenge brief: [`TRP1 Challenge Week 11_ Sales Agent Evaluation Bench.md`](TRP1%20Challenge%20Week%2011_%20Sales%20Agent%20Evaluation%20Bench.md)
- Tenacious style guide + good/bad examples: [`Tenacious Style Guide and 12 Good-Bad Examples v2.md`](Tenacious%20Style%20Guide%20and%2012%20Good-Bad%20Examples%20v2.md)
- Audit memo: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology: [`docs/methodology.md`](docs/methodology.md)
- Datasheet: [`docs/datasheet.md`](docs/datasheet.md)
- Evaluator: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Sample score report: [`reports/sample_scores.jsonl`](reports/sample_scores.jsonl)
- Interim contamination report: [`reports/contamination_check.json`](reports/contamination_check.json)
- Cost log: [`reports/cost_log.md`](reports/cost_log.md)

## What Is Next (Acts III–V)

1. Train and calibrate Path B critic/judge using preference pairs derived from the corpus + evaluator.
2. Publish HuggingFace dataset + model cards (pinned versions), blog post, and community engagement artifact.
