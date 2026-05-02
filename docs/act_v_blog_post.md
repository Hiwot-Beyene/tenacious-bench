# What τ²-Style Benches Miss About B2B Sales—And What I Built Instead

**Hiwot Beyene** · Published: [Substack](https://hiwotbeyene.substack.com/p/what-style-benches-miss-about-b2b)

See the live post for the full 1,200–2,000 word version. This file is the Markdown source kept in-repo for graders and reproducibility.

**Thesis:** Public benchmarks excel at tool-use and trajectory completion (e.g. retail-style τ²-Bench). Tenacious-Bench v0.1 targets **B2B outbound policy**: weak-signal calibration, bench/capacity honesty, tone markers, CRM overrides, and non-condescending gap framing—mechanically scored in `scoring_evaluator.py`.

**Path B:** DPO + LoRA critic on `preferences.jsonl`; adapter on [Hugging Face](https://huggingface.co/hiwot-beyene/tenacious-bench-lora). Dataset: [hiwot-beyene/tenacious-bench-v0.1](https://huggingface.co/datasets/hiwot-beyene/tenacious-bench-v0.1). Code: [GitHub](https://github.com/Hiwot-Beyene/tenacious-bench).

**Honest results:** Held-out preference ablations may be underpowered at small *n*; Delta A/B and CIs belong in `reports/ablation_results.json` and the model card—report what you measure.
