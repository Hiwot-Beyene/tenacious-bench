#!/usr/bin/env python3
"""Verify Path B training_data only references train tasks; HE-slice similarity vs dev/held."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.critic_prompt import build_critic_prompt  # noqa: E402
from evaluation.scoring_evaluator import score_task  # noqa: E402
from generation.contamination_check import bow_counts, cosine_bow, high_entropy_slice  # noqa: E402


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _dim_score(res: Dict[str, Any], name: str) -> Optional[float]:
    for d in res.get("dimensions") or []:
        if d.get("name") == name:
            return float(d["score"])
    return None


def _slice_ngrams(text: str, n: int) -> Set[str]:
    toks = text.split()
    if len(toks) < n:
        return set()
    return {" ".join(toks[i : i + n]) for i in range(len(toks) - n + 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preferences", type=Path, default=REPO_ROOT / "training_data" / "preferences.jsonl")
    ap.add_argument("--train-jsonl", type=Path, default=REPO_ROOT / "data" / "tasks_train.jsonl")
    ap.add_argument("--dev-jsonl", type=Path, default=REPO_ROOT / "data" / "tasks_dev.jsonl")
    ap.add_argument("--heldout-jsonl", type=Path, default=REPO_ROOT / "data" / "tasks_heldout.jsonl")
    ap.add_argument("--embedding-threshold", type=float, default=0.85)
    ap.add_argument("--ngram-n", type=int, default=8)
    args = ap.parse_args()

    if not args.preferences.exists():
        raise SystemExit(f"missing {args.preferences}; run scripts/build_path_b_preferences.py first")

    train_rows = {r["task_id"]: r for r in iter_jsonl(args.train_jsonl)}
    train_ids: Set[str] = set(train_rows.keys())
    dev_rows = list(iter_jsonl(args.dev_jsonl))
    held_rows = list(iter_jsonl(args.heldout_jsonl))

    dev_held_union: Set[str] = set()
    for r in dev_rows + held_rows:
        dev_held_union |= _slice_ngrams(high_entropy_slice(r), args.ngram_n)

    errs: List[str] = []
    for line in args.preferences.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        tid = rec.get("source_task_id")
        if tid not in train_ids:
            errs.append(f"pair references non-train task_id: {tid}")
            continue
        task = train_rows[tid]
        prompt = rec.get("prompt") or ""
        if build_critic_prompt(task) != prompt:
            errs.append(f"prompt mismatch for {tid} (rebuild preferences)")
            continue
        chosen = rec.get("chosen") or ""
        rejected = rec.get("rejected") or ""
        cr = score_task(task, chosen)
        rr = score_task(task, rejected)
        if cr.get("error"):
            errs.append(f"chosen score error for {tid}: {cr.get('error')}")
        elif not cr.get("pass"):
            errs.append(f"chosen must pass evaluator for {tid}")
        if rr.get("error"):
            errs.append(f"rejected score error for {tid}: {rr.get('error')}")
        elif rr.get("pass"):
            errs.append(f"rejected must not pass global threshold for {tid}")
        tdim = rec.get("target_violation_dimension")
        if isinstance(tdim, str) and tdim:
            ts = _dim_score(rr, tdim)
            if ts is None:
                errs.append(f"rejected missing dimension {tdim!r} in scorer output for {tid}")
            elif ts > 1.0:
                errs.append(
                    f"rejected must violate target dimension {tdim!r} (score<=1), got {ts} for {tid}"
                )
        he_train = high_entropy_slice(task)
        if _slice_ngrams(he_train, args.ngram_n) & dev_held_union:
            errs.append(f"high_entropy {args.ngram_n}-gram overlap train task {tid} vs dev/held pool")

        hb = bow_counts(he_train)
        for peer in dev_rows + held_rows:
            c = cosine_bow(hb, bow_counts(high_entropy_slice(peer)))
            if c >= args.embedding_threshold:
                errs.append(
                    f"HE cosine {c:.4f} >= {args.embedding_threshold}: train {tid} vs {peer.get('task_id')}"
                )
                break

    if errs:
        print("TRAINING DATA LEAKAGE CHECK FAIL:\n" + "\n".join(errs[:40]))
        if len(errs) > 40:
            print(f"... and {len(errs) - 40} more")
        raise SystemExit(1)
    print("training_data leakage check OK:", args.preferences)


if __name__ == "__main__":
    main()
