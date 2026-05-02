# Path memo: Prometheus 2 (Kim et al., 2024) — specialized evaluators

## What transfers

Prometheus argues for **task-specific rubric-conditioned** evaluators instead of generic “helpfulness.” That aligns with Tenacious-Bench: we already encode rubric dimensions mechanically and use them to **gate** preference pairs.

## Where we diverge

We are **not** cloning Prometheus’ full architecture in Week 11; instead we use a **small backbone + preference tuning** (Path B) with **mechanical pre-labels** from `scoring_evaluator.py`. The disagreement is pragmatic: Prometheus-scale judge training is a research project; our deliverable is a **reject layer** with auditable training rows (`training_data/preferences.jsonl` + `manifest.json`).
