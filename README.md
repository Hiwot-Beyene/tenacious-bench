# Tenacious-Bench

Tenacious-Bench is a sales-agent evaluation bench for the Tenacious workflow domain. It targets behaviors that public benchmarks under-grade in B2B outreach: confidence calibration under weak signals, bench commitment safety, tone-marker compliance, coordination with CRM overrides, and non-condescending gap framing.

## Current Status (Week 11 Interim)

### Completed (robust core)
- Audit memo with Week 10 evidence links: [`docs/audit_memo.md`](docs/audit_memo.md)
- Methodology rationale (Path B): [`docs/methodology.md`](docs/methodology.md)
- Mechanical scoring evaluator: [`evaluation/scoring_evaluator.py`](evaluation/scoring_evaluator.py)
- Three committed example tasks: [`evaluation/tasks_examples/`](evaluation/tasks_examples/)
- Formal task schema: [`schema.json`](schema.json)
- Datasheet draft with Gebru + Pushkarna layers: [`docs/datasheet.md`](docs/datasheet.md)
- Generation pipeline scaffolds + routing policy: [`generation/`](generation/), [`generation/routing_policy.md`](generation/routing_policy.md)
- Judge prompts committed as text: [`prompts/`](prompts/)
- Two synthesis memos with evidence-backed disagreement:
  - [`synthesis_memos/memo_liu_2024_synthetic_data.md`](synthesis_memos/memo_liu_2024_synthetic_data.md)
  - [`synthesis_memos/memo_gu_llm_as_judge.md`](synthesis_memos/memo_gu_llm_as_judge.md)

### In progress
- Full dataset synthesis run (200–300 tasks)
- Inter-rater agreement report
- Contamination final report over sealed held-out
- Synthesis memos (minimum two, critical engagement)

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

1. Run generation pipeline to populate train/dev/held-out partitions with target composition.
2. Execute contamination checks and publish `reports/contamination_check.json` with resolved flags.
3. Train and calibrate Path B critic/judge against train + dev, evaluate on held-out.
4. Finalize at least two synthesis memos in `synthesis_memos/`.
5. Prepare HuggingFace dataset/model cards and publication bundle.
