#!/usr/bin/env python3
"""Split `training_data/preferences.jsonl` into train/valid JSONL for TRL/Unsloth DPO.

Writes:
  training_data/for_unsloth/train.jsonl
  training_data/for_unsloth/valid.jsonl
  training_data/for_unsloth/split_manifest.json

Usage (from tenacious-bench/):
  uv run python scripts/export_unsloth_splits.py
  uv run python scripts/export_unsloth_splits.py --valid-fraction 0.1 --seed 11711
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def _load_prefs(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _unsloth_row(p: Dict[str, Any]) -> Dict[str, str]:
    return {
        "prompt": str(p.get("prompt") or ""),
        "chosen": str(p.get("chosen") or ""),
        "rejected": str(p.get("rejected") or ""),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Export train/valid splits for preference LoRA.")
    ap.add_argument("--preferences", type=Path, default=REPO_ROOT / "training_data" / "preferences.jsonl")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "training_data" / "for_unsloth")
    ap.add_argument("--valid-fraction", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=11711)
    args = ap.parse_args()

    if not args.preferences.exists():
        raise SystemExit(f"missing {args.preferences}; run scripts/build_path_b_preferences.py first")

    rows = _load_prefs(args.preferences)
    rnd = random.Random(args.seed)
    order = list(range(len(rows)))
    rnd.shuffle(order)
    n_val = max(1, int(len(rows) * args.valid_fraction)) if len(rows) >= 10 else max(1, len(rows) // 5)
    val_set = set(order[:n_val])
    train_rows = [_unsloth_row(rows[i]) for i in range(len(rows)) if i not in val_set]
    val_rows = [_unsloth_row(rows[i]) for i in range(len(rows)) if i in val_set]
    if not train_rows:
        raise SystemExit("train split empty; lower --valid-fraction")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_p = args.out_dir / "train.jsonl"
    val_p = args.out_dir / "valid.jsonl"
    for path, data in ((train_p, train_rows), (val_p, val_rows)):
        with path.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_preferences": str(args.preferences.relative_to(REPO_ROOT)),
        "n_total": len(rows),
        "n_train": len(train_rows),
        "n_valid": len(val_rows),
        "valid_fraction": args.valid_fraction,
        "seed": args.seed,
    }
    (args.out_dir / "split_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
