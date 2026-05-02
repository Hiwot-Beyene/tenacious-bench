#!/usr/bin/env python3
"""
Sealed held-out ablations for Act IV (Path B log-prob preference accuracy).

Writes:
  reports/ablation_results.json   — summary + bootstrap CIs (from this run, not hand-authored)
  reports/held_out_traces.jsonl — one JSON object per scored (pair × condition)

Conditions (same backbone):
  baseline      — base weights, no LoRA, no extra system message
  trained       — base + PEFT adapter (the trained preference signal)
  prompt_only   — base weights + system instruction (Delta B: prompt-engineered control only)

Delta A: trained vs baseline (paired bootstrap on per-pair correctness, 95% CI + p-values).
Delta B: trained vs prompt_only (same backbone; no adapter on prompt_only path).
Delta C: informational only; pass --tau2-week10-score if you have a Week 10 number on file
         (no τ² re-run per Week 11 rules).
Cost–Pareto: wall time (ms) + completion token counts per condition for downstream 2D analysis.

All four comparisons are selected via --comparisons (default `all`) from one entrypoint; per-pair
scoring uses visible try/except so one bad example does not abort the harness.

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
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

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

COMPARISON_DELTA_A = "delta_a"
COMPARISON_DELTA_B = "delta_b"
COMPARISON_DELTA_C = "delta_c"
COMPARISON_COST_PARETO = "cost_pareto"
ALL_COMPARISONS: Tuple[str, ...] = (
    COMPARISON_DELTA_A,
    COMPARISON_DELTA_B,
    COMPARISON_DELTA_C,
    COMPARISON_COST_PARETO,
)


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _parse_comparisons(spec: str) -> Tuple[str, ...]:
    s = spec.strip().lower()
    if s == "all":
        return ALL_COMPARISONS
    parts = tuple(p.strip().lower() for p in spec.split(",") if p.strip())
    valid = set(ALL_COMPARISONS)
    bad = [p for p in parts if p not in valid]
    if bad:
        raise SystemExit(f"unknown --comparisons entries {bad}; use comma-separated from {sorted(valid)} or 'all'")
    if not parts:
        raise SystemExit("--comparisons must be 'all' or a non-empty comma list")
    return parts


def _conditions_needed(comparisons: Sequence[str]) -> Set[str]:
    """Minimal model-scoring conditions required for the selected comparisons."""
    need: Set[str] = set()
    cset = set(comparisons)
    if COMPARISON_DELTA_A in cset or COMPARISON_COST_PARETO in cset:
        need.add("baseline")
    if COMPARISON_DELTA_B in cset or COMPARISON_COST_PARETO in cset:
        need.add("prompt_only")
    if (
        COMPARISON_DELTA_A in cset
        or COMPARISON_DELTA_B in cset
        or COMPARISON_COST_PARETO in cset
    ):
        need.add("trained")
    return need


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
    """Bootstrap mean(other - baseline) with replacement over pairs; 95% CI; one- and two-sided p vs 0."""
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
    p_two_sided = min(1.0, 2.0 * p_one_sided)
    return {
        "mean_delta_accuracy": float(obs),
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "p_value_paired_bootstrap_one_sided": p_one_sided,
        "p_value_paired_bootstrap_two_sided": p_two_sided,
        "n_bootstrap": float(n_boot),
    }


def build_delta_c_informational(week10_score: Optional[float]) -> Dict[str, Any]:
    """Delta C without re-running τ²-Bench (Week 11 informational slot)."""
    return {
        "week10_score_on_file": week10_score,
        "trained_score": None,
        "note": "Per Week 11 rules: do not re-run τ² this week; compare to Week 10 score informationally only.",
    }


def _cost_for_condition(traces: List[Dict[str, Any]], condition: str) -> Dict[str, float]:
    rel = [r for r in traces if r.get("condition") == condition and r.get("error") is None]
    if not rel:
        return {
            "ms_per_pair_mean": 0.0,
            "completion_tokens_mean": 0.0,
            "wall_time_ms_total": 0.0,
            "completion_tokens_total": 0.0,
            "n_scored_pairs": 0.0,
        }
    toks = [float(r["completion_tokens"]) for r in rel]
    lats = [float(r["latency_ms"]) for r in rel]
    return {
        "ms_per_pair_mean": float(np.mean(lats)),
        "completion_tokens_mean": float(np.mean(toks)),
        "wall_time_ms_total": float(np.sum(lats)),
        "completion_tokens_total": float(np.sum(toks)),
        "n_scored_pairs": float(len(rel)),
    }


def _append_failure_traces(
    traces: List[Dict[str, Any]],
    *,
    pair_ix: int,
    row: Dict[str, Any],
    conditions: Set[str],
    err: BaseException,
) -> None:
    tb = traceback.format_exc()
    base = {
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pair_index": pair_ix,
        "source_task_id": row.get("source_task_id"),
        "failure_dimension": row.get("failure_dimension"),
        "error": repr(err),
        "error_type": type(err).__name__,
        "traceback": tb,
    }
    for cond in sorted(conditions):
        traces.append({**base, "condition": cond, "correct": None, "completion_tokens": None, "latency_ms": None})


def run_scoring_loop(
    *,
    model: Any,
    tokenizer: Any,
    device: Any,
    rows: List[Dict[str, Any]],
    prompt_only_system: str,
    needed: Set[str],
) -> Tuple[List[int], List[int], List[int], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Score held-out pairs; return parallel correct lists (only for successful pairs — same length)
    and traces. failure_summary counts exceptions.
    """
    import torch

    bl_correct: List[int] = []
    tr_correct: List[int] = []
    po_correct: List[int] = []
    traces: List[Dict[str, Any]] = []
    n_fail = 0

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
                "error": None,
            }
        )

    with torch.inference_mode():
        for i, row in enumerate(rows):
            prompt, ch, rej = row["prompt"], row["chosen"], row["rejected"]
            try:
                ps_b = ps_t = ps_p = None
                if "baseline" in needed:
                    with model.disable_adapter():
                        ps_b = score_preference_pair(
                            model,
                            tokenizer,
                            prompt=prompt,
                            chosen=ch,
                            rejected=rej,
                            device=device,
                            system=None,
                        )
                if "prompt_only" in needed:
                    with model.disable_adapter():
                        ps_p = score_preference_pair(
                            model,
                            tokenizer,
                            prompt=prompt,
                            chosen=ch,
                            rejected=rej,
                            device=device,
                            system=prompt_only_system,
                        )
                if "trained" in needed:
                    ps_t = score_preference_pair(
                        model,
                        tokenizer,
                        prompt=prompt,
                        chosen=ch,
                        rejected=rej,
                        device=device,
                        system=None,
                    )
                if "baseline" in needed and ps_b is not None:
                    bl_correct.append(ps_b.correct)
                    emit("baseline", i, row, ps_b)
                if "prompt_only" in needed and ps_p is not None:
                    po_correct.append(ps_p.correct)
                    emit("prompt_only", i, row, ps_p)
                if "trained" in needed and ps_t is not None:
                    tr_correct.append(ps_t.correct)
                    emit("trained", i, row, ps_t)
            except Exception as exc:  # noqa: BLE001 — visible harness failure path
                n_fail += 1
                _append_failure_traces(
                    traces,
                    pair_ix=i,
                    row=row,
                    conditions=needed,
                    err=exc,
                )

    failure_summary = {
        "pairs_failed": n_fail,
        "pairs_total": len(rows),
        "note": "Failed pairs append traceback rows; bootstrap uses only successful aligned lists.",
    }
    return bl_correct, tr_correct, po_correct, traces, failure_summary


def assemble_results(
    *,
    comparisons: Tuple[str, ...],
    n_rows: int,
    model_id: str,
    adapter: Path,
    device: str,
    bl_correct: List[int],
    tr_correct: List[int],
    po_correct: List[int],
    traces: List[Dict[str, Any]],
    failure_summary: Dict[str, Any],
    prompt_only_system_excerpt: str,
    bootstrap_samples: int,
    bootstrap_seed: int,
    tau2_week10: Optional[float],
) -> Dict[str, Any]:
    """Build ablation_results.json from scored lists (shared interface for all comparisons)."""
    results: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "comparisons_run": list(comparisons),
        "n_pairs_input": n_rows,
        "model_id": model_id,
        "adapter": str(adapter),
        "device": device,
        "harness": {
            "path": "B",
            "delta_a_definition": "trained (PEFT adapter) vs baseline (adapter disabled, no system prompt)",
            "delta_b_definition": "trained vs prompt_only (same backbone, adapter off; instruction-only control)",
            "delta_c_definition": "informational τ² Week 10 score only (no re-run)",
            "failure_handling": "try/except per pair; errors recorded in held_out_traces.jsonl",
        },
        "scoring_failures": failure_summary,
        "delta_b_prompt_control_excerpt": prompt_only_system_excerpt[:500]
        + ("…" if len(prompt_only_system_excerpt) > 500 else ""),
    }

    if COMPARISON_DELTA_A in comparisons:
        n = len(bl_correct)
        if n != len(tr_correct):
            results["delta_a_trained_vs_baseline"] = {
                "error": "misaligned paired lists after failures",
                "n_baseline": len(bl_correct),
                "n_trained": len(tr_correct),
            }
        elif n == 0:
            results["delta_a_trained_vs_baseline"] = {"error": "no successful pairs for delta_a"}
        else:
            acc_bl = sum(bl_correct) / n
            acc_tr = sum(tr_correct) / n
            results["accuracies_baseline_trained_slice"] = {"baseline": acc_bl, "trained": acc_tr, "n": n}
            results["delta_a_trained_vs_baseline"] = {
                "description": "Paired bootstrap on per-pair correctness (trained - baseline).",
                **paired_bootstrap(bl_correct, tr_correct, n_boot=bootstrap_samples, seed=bootstrap_seed),
            }

    if COMPARISON_DELTA_B in comparisons:
        n = len(po_correct)
        if n != len(tr_correct):
            results["delta_b_trained_vs_prompt_only"] = {
                "error": "misaligned paired lists after failures",
                "n_prompt_only": len(po_correct),
                "n_trained": len(tr_correct),
            }
        elif n == 0:
            results["delta_b_trained_vs_prompt_only"] = {"error": "no successful pairs for delta_b"}
        else:
            acc_po = sum(po_correct) / n
            acc_tr = sum(tr_correct) / n
            results["accuracies_prompt_only_trained_slice"] = {
                "prompt_only": acc_po,
                "trained": acc_tr,
                "n": n,
            }
            results["delta_b_trained_vs_prompt_only"] = {
                "description": "Paired bootstrap (trained - prompt_only), same backbone.",
                **paired_bootstrap(
                    po_correct,
                    tr_correct,
                    n_boot=bootstrap_samples,
                    seed=bootstrap_seed + 1,
                ),
            }

    if COMPARISON_DELTA_C in comparisons:
        results["delta_c_tau2_retail"] = build_delta_c_informational(tau2_week10)

    if COMPARISON_COST_PARETO in comparisons:
        results["cost_pareto"] = {
            "baseline": _cost_for_condition(traces, "baseline"),
            "trained": _cost_for_condition(traces, "trained"),
            "prompt_only": _cost_for_condition(traces, "prompt_only"),
            "instrumentation": "wall_clock_ms per pair + sum of completion tokens (chosen+rejected) per pair",
        }

    return results


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
    ap.add_argument(
        "--comparisons",
        type=str,
        default="all",
        help="Comma list: delta_a,delta_b,delta_c,cost_pareto — or 'all' (default).",
    )
    ap.add_argument("--bootstrap-samples", type=int, default=10_000)
    ap.add_argument("--bootstrap-seed", type=int, default=11711)
    ap.add_argument("--out-results", type=Path, default=REPO_ROOT / "reports" / "ablation_results.json")
    ap.add_argument("--out-traces", type=Path, default=REPO_ROOT / "reports" / "held_out_traces.jsonl")
    args = ap.parse_args()

    silence_hub_http_noise()
    comparisons = _parse_comparisons(args.comparisons)
    needed = _conditions_needed(comparisons)

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
    if COMPARISON_DELTA_B in comparisons or COMPARISON_COST_PARETO in comparisons:
        if not prompt_only_system:
            raise SystemExit(
                "Delta B / cost_pareto need prompt_only scoring; add training_data/delta_b_control_system.txt "
                "or pass --prompt-only-system / --prompt-only-system-file."
            )

    only_delta_c = comparisons == (COMPARISON_DELTA_C,)
    if only_delta_c:
        n_hint = sum(1 for _ in _iter_jsonl(args.pairs)) if args.pairs.exists() else 0
        results = assemble_results(
            comparisons=comparisons,
            n_rows=n_hint,
            model_id=args.model_id,
            adapter=args.adapter,
            device="n/a",
            bl_correct=[],
            tr_correct=[],
            po_correct=[],
            traces=[],
            failure_summary={
                "pairs_failed": 0,
                "pairs_total": n_hint,
                "note": "delta_c only — no model scoring; n_pairs_input counts held-out JSONL rows when present.",
            },
            prompt_only_system_excerpt=prompt_only_system or "",
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            tau2_week10=args.tau2_week10_score,
        )
        args.out_results.parent.mkdir(parents=True, exist_ok=True)
        args.out_results.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"wrote": str(args.out_results), "mode": "delta_c_only"}, indent=2))
        return

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
    bl_correct, tr_correct, po_correct, traces, failure_summary = run_scoring_loop(
        model=model,
        tokenizer=tokenizer,
        device=device,
        rows=rows,
        prompt_only_system=prompt_only_system,
        needed=needed,
    )

    args.out_traces.parent.mkdir(parents=True, exist_ok=True)
    with args.out_traces.open("w", encoding="utf-8") as trace_f:
        for rec in traces:
            trace_f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    results = assemble_results(
        comparisons=comparisons,
        n_rows=len(rows),
        model_id=args.model_id,
        adapter=args.adapter,
        device=str(device),
        bl_correct=bl_correct,
        tr_correct=tr_correct,
        po_correct=po_correct,
        traces=traces,
        failure_summary=failure_summary,
        prompt_only_system_excerpt=prompt_only_system,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        tau2_week10=args.tau2_week10_score,
    )

    if COMPARISON_DELTA_A in comparisons and "delta_a_trained_vs_baseline" in results:
        acc = results.get("accuracies_baseline_trained_slice")
        if acc:
            results.setdefault("accuracies", {})["baseline"] = acc["baseline"]
            results["accuracies"]["trained"] = acc["trained"]
    if COMPARISON_DELTA_B in comparisons and "accuracies_prompt_only_trained_slice" in results:
        acc = results["accuracies_prompt_only_trained_slice"]
        results.setdefault("accuracies", {})["prompt_only"] = acc["prompt_only"]
        results["accuracies"]["trained"] = acc["trained"]

    args.out_results.parent.mkdir(parents=True, exist_ok=True)
    args.out_results.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(args.out_results), "wrote_traces": str(args.out_traces)}, indent=2))


if __name__ == "__main__":
    main()
