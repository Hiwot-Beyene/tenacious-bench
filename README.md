# Tenacious-Bench

Tenacious-Bench is a sales-agent evaluation bench for the Tenacious workflow domain. It targets behaviors that public benchmarks under-grade in B2B outreach: confidence calibration under weak signals, bench commitment safety, tone-marker compliance, coordination with CRM overrides, and non-condescending gap framing.

## Current Status (Week 11 Interim)

### Completed (robust core)
- Audit memo with Week 10 evidence links: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology rationale (Path B): [`docs/methodology.md`](docs/methodology.md)
- Mechanical scoring evaluator: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Example tasks (incl. adversarial fail fixture): [`evaluation/tasks_examples/`](evaluation/tasks_examples/)
- Formal task schema: [`schema.json`](schema.json)
- Datasheet draft with Gebru + Pushkarna layers: [`docs/datasheet.md`](docs/datasheet.md)
- **Materialized v0.1 corpus (240 tasks)** + verifier: [`data/`](data/), [`scripts/materialize_corpus.py`](scripts/materialize_corpus.py), [`scripts/verify_composition.py`](scripts/verify_composition.py), [`reports/composition_crosstab.md`](reports/composition_crosstab.md)
- **Inter-rater agreement (n=30)**: [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md), [`reports/inter_rater/`](reports/inter_rater/), [`scripts/compute_inter_rater_agreement.py`](scripts/compute_inter_rater_agreement.py)
- Interim report (PDF source): [`reports/interim_report.md`](reports/interim_report.md)
- Generation pipeline scaffolds + routing policy: [`generation/`](generation/), [`generation/routing_policy.md`](generation/routing_policy.md)
- Judge prompts committed as text: [`prompts/`](prompts/)
- Two synthesis memos with evidence-backed disagreement:
  - [`synthesis_memos/memo_liu_2024_synthetic_data.md`](synthesis_memos/memo_liu_2024_synthetic_data.md)
  - [`synthesis_memos/memo_gu_llm_as_judge.md`](synthesis_memos/memo_gu_llm_as_judge.md)

### In progress
- Contamination final report over sealed held-out (publication gate)
- Path B training run + HuggingFace dataset/model cards

## Challenge Requirement Mapping (Reviewer Fast Path)

This section maps each Week 11 interim requirement directly to committed artifacts so the repo can be graded without searching.

| Challenge requirement | Primary artifact(s) |
|---|---|
| Audit memo with Week 10 evidence | [`docs/audit_memo.md`](docs/audit_memo.md) |
| Scoring evaluator with mechanical decomposition + error handling | [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py), [`evaluation/tasks_examples/`](evaluation/tasks_examples/) |
| Generation pipeline, routing, judge filter | [`generation/generate_tasks.py`](generation/generate_tasks.py), [`generation/judge_filter.py`](generation/judge_filter.py), [`generation/dedup_pairwise.py`](generation/dedup_pairwise.py), [`generation/contamination_check.py`](generation/contamination_check.py), [`generation/routing_policy.md`](generation/routing_policy.md) |
| Datasheet (Gebru + Pushkarna layers) | [`docs/datasheet.md`](docs/datasheet.md) |
| Methodology rationale (Path B + citations + contamination protocol) | [`docs/methodology.md`](docs/methodology.md) |
| Synthesis memos with critical engagement | [`synthesis_memos/memo_liu_2024_synthetic_data.md`](synthesis_memos/memo_liu_2024_synthetic_data.md), [`synthesis_memos/memo_gu_llm_as_judge.md`](synthesis_memos/memo_gu_llm_as_judge.md) |
| Interim report + composition + inter-rater | [`reports/interim_report.md`](reports/interim_report.md), [`reports/composition_crosstab.md`](reports/composition_crosstab.md), [`reports/composition_actual.json`](reports/composition_actual.json), [`reports/inter_rater_agreement.md`](reports/inter_rater_agreement.md), [`reports/inter_rater/`](reports/inter_rater/), [`reports/sample_scores.jsonl`](reports/sample_scores.jsonl), [`reports/contamination_check.json`](reports/contamination_check.json) |
| Materialized dataset + scripts | [`data/tasks_all.jsonl`](data/tasks_all.jsonl), [`scripts/materialize_corpus.py`](scripts/materialize_corpus.py), [`scripts/verify_composition.py`](scripts/verify_composition.py), [`scripts/compute_inter_rater_agreement.py`](scripts/compute_inter_rater_agreement.py) |

Suggested review order (10-minute pass):
1. `README.md` (this file)
2. `docs/audit_memo.md` and `docs/methodology.md`
3. `evaluation/scoring_evaluator.py` and `evaluation/tasks_examples/*.json`
4. `docs/datasheet.md`
5. `data/tasks_all.jsonl` + `reports/composition_crosstab.md`
6. `reports/inter_rater_agreement.md` + `reports/interim_report.md`

## Materialize corpus and verify composition

```bash
python scripts/materialize_corpus.py
python scripts/verify_composition.py
python scripts/compute_inter_rater_agreement.py
```

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
- `data/` - materialized task JSONL (train/dev/heldout/all)
- `scripts/` - corpus materialization, composition verification, inter-rater tooling
- `evaluation/` - scoring evaluator and example tasks
- `schema.json` - canonical task object contract for examples and generated tasks
- `generation/` - synthesis, judge filter, dedup, contamination scaffolds
- `prompts/` - judge prompt text files (pointwise + pairwise)
- `reports/` - run reports (contamination, scoring outputs, cost logs)
- `synthesis_memos/` - paper memos with evidence-backed disagreements

## Major Artifact Links

- Week 11 challenge brief: [`TRP1 Challenge Week 11_ Sales Agent Evaluation Bench.md`](TRP1%20Challenge%20Week%2011_%20Sales%20Agent%20Evaluation%20Bench.md)
- Tenacious style guide + good/bad examples: [`Tenacious Style Guide and 12 Good-Bad Examples v2.md`](Tenacious%20Style%20Guide%20and%2012%20Good-Bad%20Examples%20v2.md)
- Audit memo: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology: [`docs/methodology.md`](docs/methodology.md)
- Datasheet: [`docs/datasheet.md`](docs/datasheet.md)
- Evaluator: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Sample score report: [`reports/sample_scores.jsonl`](reports/sample_scores.jsonl)
- Interim contamination report: [`reports/contamination_check.json`](reports/contamination_check.json)
- Cost log: [`reports/cost_log.md`](reports/cost_log.md)

## What Is Next

1. Execute full contamination checks on sealed held-out and publish resolved `reports/contamination_check.json`.
2. Train and calibrate Path B critic/judge using preference pairs derived from the corpus + evaluator.
3. Publish HuggingFace dataset + model cards (pinned versions).
