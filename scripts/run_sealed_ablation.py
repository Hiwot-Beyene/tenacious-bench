#!/usr/bin/env python3
"""
Sealed held-out ablations for Act IV (Path B log-prob preference accuracy).

Writes:
  reports/ablation_results.json   — summary + bootstrap CIs (from this run, not hand-authored)
  reports/held_out_traces.jsonl — one JSON object per scored (pair × condition)

Conditions (same backbone):
  baseline      — base weights, no LoRA, no extra system message
  trained       — base + PEFT adapter
  prompt_only   — base weights + system instruction (Delta B control)

Delta A: trained vs baseline (paired bootstrap on per-example correctness).
Delta B: trained vs prompt_only.
Delta C: informational only; pass --tau2-week10-score if you have a Week 10 number on file.

Usage:
  cd tenacious-bench
  uv sync --extra train
  uv run python scripts/build_heldout_eval_pairs.py
  uv run python scripts/run_sealed_ablation.py --adapter outputs/preference_lora/lora_adapter

Default Delta B system text: training_data/delta_b_control_system.txt (override with --prompt-only-system-file).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from evaluation.critic_logprob import completion_neg_log_loss  # noqa: E402
from evaluation.hub_quiet import silence_hub_http_noise  # noqa: E402


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


@dataclass
class PairScore:
    correct: int
    nll_chosen: float
    nll_rejected: float
    tok_chosen: int
    tok_rejected: int
    latency_ms: float


def score_preference_pair(
    model: Any,
    tokenizer: Any,
    *,
    prompt: str,
    chosen: str,
    rejected: str,
    device: Any,
    system: Optional[str],
) -> PairScore:
    t0 = time.perf_counter()
    nc, tc = completion_neg_log_loss(
        model, tokenizer, prompt=prompt, completion=chosen, device=device, system=system
    )
    nr, tr = completion_neg_log_loss(
        model, tokenizer, prompt=prompt, completion=rejected, device=device, system=system
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return PairScore(
        correct=1 if nc < nr else 0,
        nll_chosen=nc,
        nll_rejected=nr,
        tok_chosen=tc,
        tok_rejected=tr,
        latency_ms=latency_ms,
    )


def paired_bootstrap(
    baseline: Sequence[int],
    other: Sequence[int],
    *,
    n_boot: int,
    seed: int,
) -> Dict[str, float]:
    """Bootstrap mean(other - baseline) with replacement over pairs (one-sided p vs 0)."""
    a = np.asarray(baseline, dtype=np.int64)
    b = np.asarray(other, dtype=np.int64)
    d = b - a
    n = len(d)
    if n == 0:
        raise ValueError("empty paired sample")
    obs = float(d.mean())
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        means[i] = float(d[idx].mean())
    ci_low, ci_high = np.percentile(means, [2.5, 97.5])
    if obs > 0:
        p_one_sided = float(np.mean(means <= 0.0))
    else:
        p_one_sided = float(np.mean(means >= 0.0))
    return {
        "mean_delta_accuracy": float(obs),
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "p_value_paired_bootstrap_one_sided": p_one_sided,
        "n_bootstrap": float(n_boot),
    }


def _cost_for_condition(traces: List[Dict[str, Any]], condition: str) -> Dict[str, float]:
    rel = [r for r in traces if r["condition"] == condition]
    if not rel:
        return {"ms_per_pair_mean": 0.0, "completion_tokens_mean": 0.0}
    return {
        "ms_per_pair_mean": float(np.mean([r["latency_ms"] for r in rel])),
        "completion_tokens_mean": float(np.mean([r["completion_tokens"] for r in rel])),
    }


def main() -> None:
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        raise SystemExit(
            "Install train extras: cd tenacious-bench && uv sync --extra train\n" f"{e}"
        ) from e

    ap = argparse.ArgumentParser(description="Held-out sealed ablations (Path B).")
    ap.add_argument("--pairs", type=Path, default=REPO_ROOT / "reports" / "heldout_preference_pairs.jsonl")
    ap.add_argument(
        "--model-id",
        type=str,
        default="Qwen/Qwen2.5-0.5B-Instruct",
        help="Must match training backbone.",
    )
    ap.add_argument(
        "--adapter",
        type=Path,
        default=REPO_ROOT / "outputs" / "preference_lora" / "lora_adapter",
        help="PEFT adapter directory from training/preference_lora_train.py",
    )
    ap.add_argument("--prompt-only-system", type=str, default="", help="Inline system message for Delta B (optional).")
    ap.add_argument(
        "--prompt-only-system-file",
        type=Path,
        default=None,
        help="Defaults to training_data/delta_b_control_system.txt when present.",
    )
    ap.add_argument("--tau2-week10-score", type=float, default=None, help="Optional Week 10 τ²-Bench retail held-out score.")
    ap.add_argument("--bootstrap-samples", type=int, default=10_000)
    ap.add_argument("--bootstrap-seed", type=int, default=11711)
    ap.add_argument("--out-results", type=Path, default=REPO_ROOT / "reports" / "ablation_results.json")
    ap.add_argument("--out-traces", type=Path, default=REPO_ROOT / "reports" / "held_out_traces.jsonl")
    args = ap.parse_args()

    silence_hub_http_noise()

    if not args.pairs.exists():
        raise SystemExit(f"missing {args.pairs}; run scripts/build_heldout_eval_pairs.py")

    default_sys_file = REPO_ROOT / "training_data" / "delta_b_control_system.txt"
    sys_file = args.prompt_only_system_file
    if sys_file is None and default_sys_file.exists():
        sys_file = default_sys_file
    prompt_only_system = args.prompt_only_system.strip()
    if sys_file is not None:
        if not sys_file.exists():
            raise SystemExit(f"missing {sys_file}")
        prompt_only_system = sys_file.read_text(encoding="utf-8").strip()
    if not prompt_only_system:
        raise SystemExit(
            "Delta B needs a non-empty system prompt: use training_data/delta_b_control_system.txt "
            "or pass --prompt-only-system / --prompt-only-system-file."
        )

    if not args.adapter.exists():
        raise SystemExit(
            f"missing adapter {args.adapter}; train first with training/preference_lora_train.py "
            "or pass --adapter to an existing PEFT export."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch_dtype = torch.bfloat16 if device.type == "cuda" and torch.cuda.is_bf16_supported() else torch.float32

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    load_kw: Dict[str, Any] = dict(trust_remote_code=True, dtype=torch_dtype)
    if device.type == "cuda":
        load_kw["device_map"] = "auto"

    base = AutoModelForCausalLM.from_pretrained(args.model_id, **load_kw)
    if device.type == "cpu":
        base = base.to(device)
    model = PeftModel.from_pretrained(base, str(args.adapter))

    rows = list(_iter_jsonl(args.pairs))
    if not rows:
        raise SystemExit("no pairs in input")

    model.eval()

    bl_correct: List[int] = []
    tr_correct: List[int] = []
    po_correct: List[int] = []
    traces: List[Dict[str, Any]] = []

    args.out_traces.parent.mkdir(parents=True, exist_ok=True)

    def emit(condition: str, pair_ix: int, row: Dict[str, Any], ps: PairScore) -> None:
        traces.append(
            {
                "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "condition": condition,
                "pair_index": pair_ix,
                "source_task_id": row.get("source_task_id"),
                "failure_dimension": row.get("failure_dimension"),
                "correct": ps.correct,
                "nll_chosen": ps.nll_chosen,
                "nll_rejected": ps.nll_rejected,
                "completion_tokens": ps.tok_chosen + ps.tok_rejected,
                "latency_ms": round(ps.latency_ms, 4),
            }
        )

    with torch.inference_mode():
        for i, row in enumerate(rows):
            prompt, ch, rej = row["prompt"], row["chosen"], row["rejected"]
            with model.disable_adapter():
                ps_b = score_preference_pair(
                    model, tokenizer, prompt=prompt, chosen=ch, rejected=rej, device=device, system=None
                )
                ps_p = score_preference_pair(
                    model,
                    tokenizer,
                    prompt=prompt,
                    chosen=ch,
                    rejected=rej,
                    device=device,
                    system=prompt_only_system,
                )
            ps_t = score_preference_pair(
                model, tokenizer, prompt=prompt, chosen=ch, rejected=rej, device=device, system=None
            )
            bl_correct.append(ps_b.correct)
            tr_correct.append(ps_t.correct)
            po_correct.append(ps_p.correct)
            emit("baseline", i, row, ps_b)
            emit("trained", i, row, ps_t)
            emit("prompt_only", i, row, ps_p)

    with args.out_traces.open("w", encoding="utf-8") as trace_f:
        for rec in traces:
            trace_f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    n = len(rows)
    acc_bl = sum(bl_correct) / n
    acc_tr = sum(tr_correct) / n
    acc_po = sum(po_correct) / n

    delta_a = paired_bootstrap(bl_correct, tr_correct, n_boot=args.bootstrap_samples, seed=args.bootstrap_seed)
    delta_b = paired_bootstrap(po_correct, tr_correct, n_boot=args.bootstrap_samples, seed=args.bootstrap_seed + 1)

    results: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_pairs": n,
        "model_id": args.model_id,
        "adapter": str(args.adapter),
        "device": str(device),
        "accuracies": {
            "baseline": acc_bl,
            "trained": acc_tr,
            "prompt_only": acc_po,
        },
        "delta_a_trained_vs_baseline": {
            "description": "Paired bootstrap on per-pair correctness (trained - baseline).",
            **delta_a,
        },
        "delta_b_trained_vs_prompt_only": {
            "description": "Paired bootstrap (trained - prompt_only), same backbone.",
            **delta_b,
        },
        "delta_c_tau2_retail": {
            "week10_score_on_file": args.tau2_week10_score,
            "trained_score": None,
            "note": "Per Week 11 rules: do not re-run τ² this week; trained score is out of scope here.",
        },
        "cost_pareto": {
            "baseline": _cost_for_condition(traces, "baseline"),
            "trained": _cost_for_condition(traces, "trained"),
            "prompt_only": _cost_for_condition(traces, "prompt_only"),
        },
    }

    args.out_results.parent.mkdir(parents=True, exist_ok=True)
    args.out_results.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(args.out_results), "wrote_traces": str(args.out_traces)}, indent=2))


if __name__ == "__main__":
    main()
