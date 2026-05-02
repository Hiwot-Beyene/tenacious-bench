---
language:
  - en
pretty_name: Tenacious-Bench v0.1 (tasks + Path B preferences)
license: cc-by-4.0
tags:
  - evaluation
  - sales
  - alignment
  - preference-data
  - b2b
size_categories:
  - 1K<n<10K
task_categories:
  - text-classification
---

# Tenacious-Bench v0.1

## Summary

**Tenacious-Bench** is a workflow-oriented evaluation set for **B2B sales outreach** in the Tenacious domain. It targets failure modes that generic public benchmarks under-weight: **weak-signal calibration**, **bench/capacity commitment safety**, **enterprise tone-marker compliance**, **CRM/human override coordination**, and **non-condescending gap framing**. This Hub dataset release should mirror the **train/dev/held** partitions and **Path B preference pairs** committed in the open-source builder repository.

## What to upload (mirror the Git repo)

From the project root (`tenacious-bench/`), typical shards are:

| Artifact | Description |
|----------|-------------|
| `data/tasks_train.jsonl`, `tasks_dev.jsonl`, `tasks_heldout.jsonl`, `tasks_all.jsonl` | 240 single-turn email tasks with rubric metadata |
| `training_data/preferences.jsonl` | Path B pairwise preference rows (train-partition tasks only; see leakage QA) |
| `training_data/manifest.json` | Build provenance, pair counts, evaluator hash |
| `schema.json` | Task JSON contract |
| `docs/datasheet.md` | Gebru + Pushkarna documentation (copy or link) |

Do **not** upload private API keys, `.env`, or proprietary customer payloads. Company seeds in `data/company_seeds.json` are derived from public ODM-style firmographics used in the builder pipeline—verify redaction before publishing.

## Intended use

- Training and evaluating **critics / judges** (Path B preference optimization).
- Mechanical scoring research with `evaluation/scoring_evaluator.py`.
- **Not** for unsupervised scraping of prospects or automated outbound without human review.

## Citation / source

Link the canonical repository and Week 11 challenge memo in your model card. Suggested BibTeX placeholder (replace with your Zenodo/DOI if you archive a snapshot):

```bibtex
@misc{tenacious_bench_v01,
  title = {Tenacious-Bench v0.1: B2B Sales-Agent Evaluation Tasks and Preference Data},
  year = {2026},
  howpublished = {\url{https://github.com/YOUR_ORG/tenacious-bench}},
  note = {Dataset build scripts and datasheet in repository}
}
```

## Changelog

- **v0.1** — 240 tasks, four source modes, mechanical rubric, Path B preferences from train split.

## Contact

Maintain the contact email or GitHub issues link in the Hub dataset metadata to match your organization’s policy.
