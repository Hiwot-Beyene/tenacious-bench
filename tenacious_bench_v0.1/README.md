# Tenacious-Bench v0.1 (package)

Act II layout: `train/`, `dev/`, `held_out/` shards; `datasheet.md`; `contamination_check.json`; `inter_rater_agreement.md`; `generation_scripts/` (metadata + logs).

Rebuild corpus + package:

```bash
python scripts/build_corpus.py
python scripts/run_judge_filter_pipeline.py
python scripts/build_tenacious_bench_v01_package.py
```
