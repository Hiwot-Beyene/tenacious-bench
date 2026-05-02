#!/usr/bin/env python3
"""
Preference LoRA training (Path B) using Hugging Face TRL DPOTrainer.

Pin the backbone to match the Week 11 stack (Qwen3.5 0.8B / 2B / 4B Instruct on HF).
Default fallback: Qwen2.5-0.5B-Instruct for dry runs when the exact id is unavailable.

Unsloth Colab: mirror hyperparameters from the official Qwen3.5 + Unsloth starter notebook
(r, alpha, dropout, LR, beta, batch/accumulation—defaults below are typical LoRA+DPO starters;
override flags to match your pinned notebook exactly).

Challenge clock (Week 11 Day 5): the published **30–90 minute** budget and **“stop at ~30 min if not
converging”** rule apply to **training steps** (loss/eval), **not** to one-time Hugging Face weight
downloads. Pre-download weights (`scripts/prefetch_hub_model.py` or shared `HF_HOME`) so that wall
clock measures learning, not bandwidth. Use a **GPU** for that budget; CPU is smoke-test only.

Artifacts:
  reports/training_run.log           — text log (hyperparameters + tail summary)
  reports/training_run_metrics.jsonl — one JSON record per `Trainer.on_log` event
  <output-dir>/training_meta.json
  <output-dir>/lora_adapter/       — PEFT adapter weights

Usage:
  cd tenacious-bench
  uv sync --extra train
  uv run python scripts/export_unsloth_splits.py
  uv run python training/preference_lora_train.py --output-dir outputs/preference_lora_run1

`for_unsloth/*.jsonl` must be regenerated with `export_unsloth_splits.py` (TRL conversational DPO rows).

Deliverable `training_run.log`: hyperparameters are logged; train/eval curves live in
`training_run_metrics.jsonl` when validation is enabled (omit `--skip-eval` for the real Day-5 run).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from evaluation.hub_quiet import silence_hub_http_noise  # noqa: E402


def _call_with_hub_heartbeat(log: logging.Logger, label: str, fn):
    """Log every ~45s while HF Hub work runs (downloads often print no lines for a long time)."""
    stop = threading.Event()

    def _beat() -> None:
        t0 = time.monotonic()
        while not stop.wait(45.0):
            log.info(
                "Still in progress: %s (elapsed %.0f s). First download can take several minutes.",
                label,
                time.monotonic() - t0,
            )

    th = threading.Thread(target=_beat, daemon=True)
    th.start()
    try:
        return fn()
    finally:
        stop.set()


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root.addHandler(sh)
    silence_hub_http_noise()


def main() -> None:
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback
        from trl import DPOConfig, DPOTrainer
    except ImportError as e:
        raise SystemExit(
            "Missing training deps. Install with:\n"
            "  cd tenacious-bench && uv sync --extra train\n"
            f"Import error: {e}"
        ) from e

    ap = argparse.ArgumentParser(description="DPO LoRA preference training (Path B).")
    ap.add_argument("--train-jsonl", type=Path, default=REPO_ROOT / "training_data" / "for_unsloth" / "train.jsonl")
    ap.add_argument("--valid-jsonl", type=Path, default=REPO_ROOT / "training_data" / "for_unsloth" / "valid.jsonl")
    ap.add_argument("--output-dir", type=Path, default=REPO_ROOT / "outputs" / "preference_lora")
    ap.add_argument(
        "--model-id",
        type=str,
        default="Qwen/Qwen2.5-0.5B-Instruct",
        help="HF hub id; replace with the pinned Week 11 backbone when training for real.",
    )
    ap.add_argument("--max-steps", type=int, default=0, help="0 = use num_train_epochs only.")
    ap.add_argument("--num-train-epochs", type=float, default=1.0)
    ap.add_argument("--per-device-train-batch-size", type=int, default=1)
    ap.add_argument("--gradient-accumulation-steps", type=int, default=8)
    ap.add_argument("--learning-rate", type=float, default=5e-6)
    ap.add_argument("--beta", type=float, default=0.1, help="DPO beta.")
    ap.add_argument("--logging-steps", type=int, default=5)
    ap.add_argument("--eval-steps", type=int, default=50)
    ap.add_argument("--save-steps", type=int, default=200)
    ap.add_argument("--log-file", type=Path, default=REPO_ROOT / "reports" / "training_run.log")
    ap.add_argument("--metrics-jsonl", type=Path, default=REPO_ROOT / "reports" / "training_run_metrics.jsonl")
    ap.add_argument(
        "--skip-eval",
        action="store_true",
        help="Do not load the validation JSONL (faster smoke runs; no eval curves).",
    )
    args = ap.parse_args()

    if not args.train_jsonl.exists():
        raise SystemExit(f"missing {args.train_jsonl}; run scripts/export_unsloth_splits.py")

    args.metrics_jsonl.parent.mkdir(parents=True, exist_ok=True)
    if args.metrics_jsonl.exists():
        args.metrics_jsonl.write_text("", encoding="utf-8")

    _setup_logging(args.log_file)
    log = logging.getLogger("train")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info("device=%s model_id=%s", device, args.model_id)
    if device == "cpu":
        log.warning(
            "CUDA is not available; training will use CPU (slow). For Day-5 runs use a GPU machine or Colab."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("HF_HOME"):
        hub_root = (args.output_dir / "hf_hub_cache").resolve()
        hub_root.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(hub_root)
        log.info(
            "HF_HOME was unset; using an isolated Hub cache at %s so this run does not wait on locks "
            "from other projects using ~/.cache/huggingface. To share one cache for all runs, set HF_HOME in .env.",
            hub_root,
        )
    else:
        log.info("Using HF_HOME from environment: %s", os.environ["HF_HOME"])
    if os.environ.get("HF_HUB_DISABLE_PROGRESS_BARS", "").lower() in ("1", "true", "yes"):
        log.warning(
            "HF_HUB_DISABLE_PROGRESS_BARS is set; tqdm download bars are hidden. Unset it to see progress on stderr."
        )

    hub_phase_t0 = time.perf_counter()

    ds = load_dataset("json", data_files={"train": str(args.train_jsonl)})["train"]
    eval_ds = None
    if not args.skip_eval and args.valid_jsonl.exists():
        eval_ds = load_dataset("json", data_files={"eval": str(args.valid_jsonl)})["eval"]

    tokenizer = _call_with_hub_heartbeat(
        log,
        f"tokenizer `{args.model_id}`",
        lambda: AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True),
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    torch_dtype = torch.bfloat16 if device == "cuda" and torch.cuda.is_bf16_supported() else torch.float32
    model_kw: Dict[str, Any] = {
        "dtype": torch_dtype,
        "trust_remote_code": True,
    }
    if device == "cuda":
        model_kw["device_map"] = "auto"
    log.info("Loading base weights `%s` (tokenizer done).", args.model_id)
    model = _call_with_hub_heartbeat(
        log,
        f"model weights `{args.model_id}`",
        lambda: AutoModelForCausalLM.from_pretrained(args.model_id, **model_kw),
    )
    if device == "cpu":
        model = model.to(torch.device("cpu"))

    hub_phase_s = time.perf_counter() - hub_phase_t0
    log.info(
        "Finished tokenizer + base model load from Hub in %.1f min. "
        "This time is NOT the Week 11 “30–90 min training” budget—only steps after "
        "`trainer.train()` starts count toward that.",
        hub_phase_s / 60.0,
    )

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    train_kw: Dict[str, Any] = dict(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        max_steps=args.max_steps if args.max_steps > 0 else -1,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        beta=args.beta,
        bf16=device == "cuda" and torch.cuda.is_bf16_supported(),
        fp16=device == "cuda" and not torch.cuda.is_bf16_supported(),
        report_to=[],
        remove_unused_columns=False,
    )
    if eval_ds is not None:
        train_kw["eval_strategy"] = "steps"
        train_kw["eval_steps"] = args.eval_steps
    else:
        train_kw["eval_strategy"] = "no"

    training_args = DPOConfig(**train_kw)

    class MetricsJsonlCallback(TrainerCallback):
        def __init__(self, path: Path):
            self.path = path

        def on_log(
            self,
            tr_args: Any,
            state: Any,
            control: Any,
            logs: Optional[Dict[str, float]] = None,
            **kwargs: Any,
        ) -> None:
            if not logs:
                return
            rec: Dict[str, Any] = {
                "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "step": int(state.global_step),
            }
            for k, v in logs.items():
                try:
                    json.dumps(v)
                    rec[k] = v
                except TypeError:
                    rec[k] = str(v)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    t0 = time.perf_counter()
    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=training_args,
        train_dataset=ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        peft_config=peft_config,
        callbacks=[MetricsJsonlCallback(args.metrics_jsonl)],
    )

    meta = {
        "started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hub_prefetch_wall_s": round(hub_phase_s, 3),
        "hf_home": os.environ.get("HF_HOME"),
        "model_id": args.model_id,
        "train_jsonl": str(args.train_jsonl),
        "valid_jsonl": str(args.valid_jsonl) if (not args.skip_eval and args.valid_jsonl.exists()) else None,
        "skip_eval": bool(args.skip_eval),
        "dpo_beta": args.beta,
        "lora_r": peft_config.r,
        "lora_alpha": peft_config.lora_alpha,
        "lora_dropout": peft_config.lora_dropout,
        "target_modules": list(peft_config.target_modules or ()),
        "num_train_epochs": args.num_train_epochs,
        "max_steps": args.max_steps,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "logging_steps": args.logging_steps,
        "eval_steps": args.eval_steps if eval_ds is not None else None,
    }
    log.info("hyperparameters %s", json.dumps(meta, indent=2))
    (args.output_dir / "training_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if args.skip_eval:
        log.warning(
            "Validation is OFF (--skip-eval). For Day-5 deliverables you need train + validation curves—"
            "re-run without --skip-eval for the core run."
        )
    log.info(
        "--- Day-5 training phase start --- "
        "Monitor train/loss and (if enabled) eval metrics in training_run_metrics.jsonl. "
        "Week 11 guidance: expect ~30–90 min total *training* wall time on GPU; if loss/eval show no "
        "useful movement by ~30 min of training, stop and audit preferences/data rather than extending compute."
    )

    t_training = time.perf_counter()
    trainer.train()
    adapter_dir = args.output_dir / "lora_adapter"
    trainer.save_model(str(adapter_dir))

    wall_s = time.perf_counter() - t0
    training_only_s = time.perf_counter() - t_training
    log_hist = trainer.state.log_history or []
    summary = {
        "finished_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "global_step": int(trainer.state.global_step),
        "wall_time_trainer_setup_plus_train_s": round(wall_s, 3),
        "wall_time_training_loop_only_s": round(training_only_s, 3),
        "hub_prefetch_wall_s": round(hub_phase_s, 3),
        "log_history_tail": log_hist[-10:],
    }
    log.info("finished %s", json.dumps(summary, indent=2))
    with args.log_file.open("a", encoding="utf-8") as fh:
        fh.write("\n--- run summary ---\n")
        fh.write(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
