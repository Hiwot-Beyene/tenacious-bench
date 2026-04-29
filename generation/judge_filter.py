"""Pointwise judge filter scaffold for candidate tasks.

Applies threshold policy on three dimensions and emits accepted/rejected sets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

THRESHOLDS = {
    "input_coherence": 4,
    "ground_truth_verifiability": 4,
    "rubric_application_clarity": 4,
}


def pass_threshold(j: Dict) -> bool:
    return all(int(j.get(k, 0)) >= v for k, v in THRESHOLDS.items())


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-file", required=True)
    ap.add_argument("--out-pass", required=True)
    ap.add_argument("--out-fail", required=True)
    args = ap.parse_args()

    rows = list(iter_jsonl(Path(args.in_file)))
    p, q = [], []
    for r in rows:
        judge = r.get("judge_scores") or {}
        (p if pass_threshold(judge) else q).append(r)

    for outp, data in ((args.out_pass, p), (args.out_fail, q)):
        out = Path(outp)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
