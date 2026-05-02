---
license: other
language:
  - en
base_model: Qwen/Qwen2.5-0.5B-Instruct  # Replace with your pinned Week 11 backbone + revision
tags:
  - peft
  - lora
  - alignment
  - dpo
pipeline_tag: text-generation
library_name: peft
---

# Tenacious-Bench Path B — Preference LoRA adapter

## Model summary

This repository holds a **PEFT LoRA adapter** trained with **TRL `DPOTrainer`** on **Tenacious-Bench** pairwise preferences (Path B). The **base causal LM is not included**; load this adapter on top of the pinned instruct backbone listed in `training_meta.json` produced by `training/preference_lora_train.py`.

**Author / maintainer:** [Hiwot Beyene](https://huggingface.co/hiwot-beyene).

**Training code:** open-source in the Tenacious-Bench repository (`training/preference_lora_train.py`).

## How to use

1. Install: `peft`, `transformers`, `torch` (match versions in your training run’s `training_meta.json` → `library_versions`).
2. Load base model from Hugging Face at the **same `model_id` and `revision`** as training.
3. `PeftModel.from_pretrained(base, "<this-repo-or-local-path>")`.

Example (adjust paths and dtype):

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_id = "Qwen/Qwen2.5-0.5B-Instruct"
adapter_id = "hiwot-beyene/tenacious-bench-lora"  # this Hub repo

tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(
    base_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(base, adapter_id)
```

## Evaluation

Held-out **log-prob preference accuracy** and **Delta A / B / C** (informational τ²) are computed by `scripts/run_sealed_ablation.py`. See `reports/ablation_results.json` and `reports/model_card.md` in the source repo.

## Limitations

- Slice-specific metrics; do not over-claim general chat quality.
- DPO improves preference margins on the training distribution; **task-level business outcomes** require separate validation.
- τ²-Bench retail scores are **informational only** for Week 11 unless you explicitly re-run with the same protocol.

## Training hyperparameters

Regenerate **`reports/model_card.md`** from artifacts:

`uv run python scripts/emit_model_card.py --training-meta outputs/<run>/training_meta.json --adapter outputs/<run>/lora_adapter`

## Files expected in this Hub repo

- `adapter_config.json`
- `adapter_model.safetensors` (or `adapter_model.bin`)
- Tokenizer files if you bundled them with `save_model`; otherwise rely on base model tokenizer.
