#!/usr/bin/env python3
"""
Build `data/judge_filter_log.jsonl`: pointwise scores (1–5), thresholds, pass/fail, fail_reasons.

- **Dev-tier bulk:** judge model is paired via `generation/model_routing.py` (never same id as bulk generator).
- **Eval-tier calibration:** exactly `CALIBRATION_SAMPLE_CAP` tasks from dev+heldout partitions use the
  eval-tier judge model id for spot-checks (mechanical scores unless OpenRouter eval is wired).

Run from `tenacious-bench/`:

  python scripts/run_judge_filter_pipeline.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from generation.judge_filter import THRESHOLDS, pass_threshold  # noqa: E402
from generation.model_routing import (  # noqa: E402
    EVAL_TIER_CALIBRATION_JUDGE,
    dev_judge_for_bulk_generator,
    effective_author_model,
)
from generation.pointwise_judge import mechanical_pointwise_scores  # noqa: E402


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def select_calibration_ids(rows: List[Dict[str, Any]], cap: int) -> Set[str]:
    pool = [r for r in rows if r.get("partition") in ("dev", "heldout")]
    pool.sort(key=lambda r: str(r.get("task_id")))
    if len(pool) <= cap:
        return {str(r["task_id"]) for r in pool}
    step = len(pool) / cap
    out: Set[str] = set()
    for i in range(cap):
        out.add(str(pool[int(i * step)]["task_id"]))
    return out


def fail_reasons_for_scores(scores: Dict[str, int]) -> List[str]:
    reasons: List[str] = []
    for k, need in THRESHOLDS.items():
        got = int(scores.get(k, 0))
        if got < need:
            reasons.append(f"{k}: score {got} < inclusion threshold {need}")
    return reasons


def main() -> None:
    ap = argparse.ArgumentParser(description="Write judge filter audit log for all corpus tasks.")
    ap.add_argument("--tasks-all", type=Path, default=REPO_ROOT / "data" / "tasks_all.jsonl")
    ap.add_argument("--out-log", type=Path, default=REPO_ROOT / "data" / "judge_filter_log.jsonl")
    ap.add_argument("--out-summary", type=Path, default=REPO_ROOT / "reports" / "judge_filter_pipeline.json")
    ap.add_argument("--calibration-cap", type=int, default=50, help="Eval-tier spot-check slots (dev+heldout).")
    args = ap.parse_args()

    if not args.tasks_all.exists():
        raise SystemExit(f"missing {args.tasks_all}; run scripts/build_corpus.py first")

    rows = list(iter_jsonl(args.tasks_all))
    calib_ids = select_calibration_ids(rows, args.calibration_cap)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    n_accept = n_reject = 0
    n_calib = 0

    args.out_log.parent.mkdir(parents=True, exist_ok=True)
    with args.out_log.open("w", encoding="utf-8") as f:
        for r in rows:
            tid = str(r.get("task_id"))
            author = effective_author_model(r)
            scores, diag = mechanical_pointwise_scores(r)
            ok = pass_threshold(scores)
            reasons = fail_reasons_for_scores(scores) if not ok else []

            is_calib = tid in calib_ids
            if is_calib:
                n_calib += 1
                judge_model = EVAL_TIER_CALIBRATION_JUDGE
                judge_tier = "eval_calibration"
            else:
                judge_model = dev_judge_for_bulk_generator(author)
                judge_tier = "dev_bulk"

            decision = "accept" if ok else "reject"
            if ok:
                n_accept += 1
            else:
                n_reject += 1

            rec = {
                "task_id": tid,
                "partition": r.get("partition"),
                "source_mode": r.get("source_mode"),
                "failure_dimension": r.get("failure_dimension"),
                "authoring_author_model": author,
                "bulk_generator_model": author,
                "judge_tier": judge_tier,
                "judge_model": judge_model,
                "judge_scores": scores,
                "judge_diagnostics": diag,
                "thresholds": dict(THRESHOLDS),
                "decision": decision,
                "fail_reasons": reasons,
                "pointwise_scale": "1-5",
                "score_source": "mechanical_template_v0.1",
                "judge_prompt_path": "prompts/judge_pointwise.md",
                "logged_at_utc": ts,
            }
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    summary = {
        "n_tasks": len(rows),
        "n_accept": n_accept,
        "n_reject": n_reject,
        "n_eval_calibration_slots": n_calib,
        "calibration_cap": args.calibration_cap,
        "thresholds": dict(THRESHOLDS),
        "eval_tier_judge_model": EVAL_TIER_CALIBRATION_JUDGE,
        "generated_at_utc": ts,
    }
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
