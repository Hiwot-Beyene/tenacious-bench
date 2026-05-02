# Synthesis: Chen et al. (EMNLP 2025) — contamination in LLM benchmarks

## Thesis I accept

Static benchmarks leak into training corpora; evaluation must pair **partitioning discipline** with **cheap overlap tests** so held-out scores mean something. N-gram and embedding gates are standard tools; the survey correctly stresses that “no overlap” must be defined on comparable representations of the task.

## Design choice I dispute (naive application)

A literal **8-gram on full task inputs** is a poor gate for **template-built** datasets: shared scenario boilerplate creates massive overlaps even when prospect-level facts are disjoint. A benchmark that fails every pair is not stricter — it is miscalibrated.

## What we implemented

`generation/contamination_check.py` separates:

1. **Exact anonymized-input equality** (train vs held-out / train vs dev) — catches true duplicates.
2. **High-entropy slice** (firmographics + public teaser) for n-grams and cosine similarity — aligns with the *intent* of Chen-style leakage tests under shared templates.
3. **Time-shift** guard when years appear in brief/bench without a documented snapshot anchor.

## Evidence

Latest report: `reports/contamination_check.json` (`schema_version` 1.2, status `pass` on v0.1; held-out checked vs train **and** dev).

## Takeaway

Contamination tooling must encode *why* a field is comparable across splits, not only *that* n-grams exist.
