"""Near-duplicate resolver: pairwise preference when `judge_scores` exist.

Tie-break order (matches `generation/routing_policy.md`):
1) rubric_application_clarity
2) ground_truth_verifiability
3) longer candidate_output (proxy for rationale coverage)
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
    prompt = str(task.get("prompt") or "").strip().lower()
    if prompt:
        return prompt
    ic = row.get("input_context") or {}
    pr = ic.get("prospect") or {}
    brief = str(ic.get("hiring_signal_brief") or "")[:240]
    parts = [str(row.get("failure_dimension")), str(pr.get("domain")), brief]
    return "|".join(parts).strip().lower()


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
        old = seen[k]
        jo, jn = old.get("judge_scores") or {}, row.get("judge_scores") or {}
        old_c = int(jo.get("rubric_application_clarity") or 0)
        new_c = int(jn.get("rubric_application_clarity") or 0)
        old_v = int(jo.get("ground_truth_verifiability") or 0)
        new_v = int(jn.get("ground_truth_verifiability") or 0)
        old_len = len(str(old.get("candidate_output") or ""))
        new_len = len(str(row.get("candidate_output") or ""))
        if (new_c, new_v, new_len) > (old_c, old_v, old_len):
            seen[k] = row

    out = Path(args.out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in seen.values():
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
