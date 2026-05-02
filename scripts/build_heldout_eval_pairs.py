#!/usr/bin/env python3
"""Build sealed held-out preference pairs for Act IV evaluation (never mixed into training).

Writes `reports/heldout_preference_pairs.jsonl` — same keys as Unsloth rows + audit fields.

Usage:
  uv run python scripts/build_heldout_eval_pairs.py
  uv run python scripts/build_heldout_eval_pairs.py --max-pairs-per-task 1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.preference_pair_generation import iter_preference_records_for_tasks  # noqa: E402


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--tasks-heldout",
        type=Path,
        default=REPO_ROOT / "data" / "tasks_heldout.jsonl",
        dest="tasks_heldout",
    )
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "reports" / "heldout_preference_pairs.jsonl")
    ap.add_argument("--max-pairs-per-task", type=int, default=1)
    args = ap.parse_args()

    tasks = [r for r in iter_jsonl(args.tasks_heldout) if r.get("partition") == "heldout"]
    if not tasks:
        tasks = list(iter_jsonl(args.tasks_heldout))

    rows: List[Dict[str, Any]] = []
    for rec in iter_preference_records_for_tasks(
        tasks,
        max_pairs_per_task=args.max_pairs_per_task,
    ):
        rows.append(
            {
                "schema_version": "1.0",
                "partition": "heldout",
                "prompt": rec["prompt"],
                "chosen": rec["chosen"],
                "rejected": rec["rejected"],
                "source_task_id": rec["source_task_id"],
                "failure_dimension": rec["failure_dimension"],
                "rejected_mutator_id": rec["rejected_mutator_id"],
                "target_violation_dimension": rec["target_violation_dimension"],
                "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    summary = {"n_pairs": len(rows), "wrote": str(args.out)}
    print(json.dumps(summary, indent=2))
    if not rows:
        raise SystemExit("no pairs built; check held-out tasks pass evaluator + mutators")


if __name__ == "__main__":
    main()
