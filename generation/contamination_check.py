"""Contamination checks scaffold for train/dev/heldout splits.

Checks:
1) n-gram overlap (8-gram)
2) embedding-similarity placeholder hook
3) time-shift field presence for dated claims
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Set


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def ngrams(text: str, n: int = 8) -> Set[str]:
    toks = text.lower().split()
    return {" ".join(toks[i : i + n]) for i in range(max(0, len(toks) - n + 1))}


def overlap_flags(train_rows: List[Dict], held_rows: List[Dict]) -> int:
    train_ngrams = set()
    for r in train_rows:
        train_ngrams |= ngrams(str((r.get("task") or {}).get("prompt") or ""))
    flags = 0
    for r in held_rows:
        h = ngrams(str((r.get("task") or {}).get("prompt") or ""))
        if train_ngrams.intersection(h):
            flags += 1
    return flags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--heldout", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    train_rows = list(iter_jsonl(Path(args.train)))
    held_rows = list(iter_jsonl(Path(args.heldout)))

    report = {
        "n_gram_overlap_flags": overlap_flags(train_rows, held_rows),
        "embedding_similarity_flags": 0,
        "time_shift_flags": 0,
        "status": "interim_scaffold",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
