"""Near-duplicate resolver scaffold.

Uses simple text hashing + pairwise preference metadata when available.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def key_for(row: Dict) -> str:
    task = row.get("task") or {}
    return str(task.get("prompt") or "").strip().lower()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-file", required=True)
    ap.add_argument("--out-file", required=True)
    args = ap.parse_args()

    seen = {}
    for row in iter_jsonl(Path(args.in_file)):
        k = key_for(row)
        if not k:
            continue
        if k not in seen:
            seen[k] = row
            continue
        # keep row with higher rubric clarity when present
        old = seen[k]
        old_c = int(((old.get("judge_scores") or {}).get("rubric_application_clarity") or 0))
        new_c = int(((row.get("judge_scores") or {}).get("rubric_application_clarity") or 0))
        if new_c > old_c:
            seen[k] = row

    out = Path(args.out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in seen.values():
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
