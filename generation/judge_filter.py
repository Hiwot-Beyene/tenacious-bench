"""Pointwise judge filter for candidate tasks (1–5 scale, inclusion >=4 on each dimension).

Aligned with `prompts/judge_pointwise.md`. Input rows must carry `judge_scores`:
`input_coherence`, `ground_truth_verifiability`, `rubric_application_clarity`.

Emits accepted/rejected JSONL; rejected rows preserve `fail_reasons` when present or synthesize
short reasons from scores vs thresholds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

THRESHOLDS = {
    # Documented inclusion policy (see `generation/routing_policy.md`).
    "input_coherence": 4,
    "ground_truth_verifiability": 4,
    "rubric_application_clarity": 4,
}


def pass_threshold(j: Dict) -> bool:
    # Missing judge fields default to 0 so malformed rows fail safely.
    return all(int(j.get(k, 0)) >= v for k, v in THRESHOLDS.items())


def _synth_fail_reasons(judge: Dict) -> List[str]:
    out: List[str] = []
    for k, need in THRESHOLDS.items():
        got = int(judge.get(k, 0))
        if got < need:
            out.append(f"{k}: {got} < {need}")
    return out


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
        ok = pass_threshold(judge)
        if not ok:
            reasons = r.get("fail_reasons")
            if not reasons:
                r = dict(r)
                r["fail_reasons"] = _synth_fail_reasons(judge)
            q.append(r)
        else:
            p.append(r)

    for outp, data in ((args.out_pass, p), (args.out_fail, q)):
        out = Path(outp)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
