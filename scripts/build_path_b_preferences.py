#!/usr/bin/env python3
"""Build Path B preference pairs from data/tasks_train.jsonl (Act III)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.critic_prompt import build_critic_prompt  # noqa: E402
from bench_corpus.preference_mutators import (  # noqa: E402
    finalize_rejected_below_threshold,
    iter_mutators_for_dimension,
    list_all_mutator_ids,
)
from evaluation.scoring_evaluator import score_task  # noqa: E402

SCHEMA_VERSION = "1.1"


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _git_head() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _dim_map(res: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for d in res.get("dimensions") or []:
        out[str(d["name"])] = float(d["score"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build training_data/preferences.jsonl for Path B.")
    ap.add_argument("--train-jsonl", type=Path, default=REPO_ROOT / "data" / "tasks_train.jsonl")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "training_data")
    ap.add_argument(
        "--min-pairs-per-dimension",
        type=int,
        default=1,
        help="Exit 1 if any failure_dimension has fewer than this many pairs.",
    )
    ap.add_argument(
        "--max-pairs-per-task",
        type=int,
        default=0,
        help="Cap mutators per task (0 = no cap).",
    )
    ap.add_argument(
        "--mutators",
        type=str,
        default="",
        help="Comma-separated mutator ids to allow (default: all). See --list-mutator-ids.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts only; do not write preferences.jsonl or manifest.json.",
    )
    ap.add_argument(
        "--list-mutator-ids",
        action="store_true",
        help="Print known mutator ids and exit.",
    )
    args = ap.parse_args()

    if args.list_mutator_ids:
        print(json.dumps({"mutator_ids": list_all_mutator_ids()}, indent=2))
        return

    allowed_ids: Optional[Set[str]] = None
    if args.mutators.strip():
        allowed_ids = {x.strip() for x in args.mutators.split(",") if x.strip()}
        known = set(list_all_mutator_ids())
        unknown = sorted(allowed_ids - known)
        if unknown:
            raise SystemExit(
                f"unknown mutator id(s): {unknown}. Known: {sorted(known)} (use --list-mutator-ids)"
            )

    eval_path = REPO_ROOT / "evaluation" / "scoring_evaluator.py"
    rows = list(iter_jsonl(args.train_jsonl))
    train_rows = [r for r in rows if r.get("partition") == "train"]
    pairs: List[Dict[str, Any]] = []
    skipped_chosen_fail = 0
    skipped_chosen_score_error = 0
    mutator_fail_by_dim: Dict[str, int] = defaultdict(int)
    skipped_finalize_fail = 0
    per_task_pair_count: Dict[str, int] = defaultdict(int)

    for task in train_rows:
        chosen = task.get("candidate_output") or ""
        cr = score_task(task, chosen)
        if cr.get("error"):
            skipped_chosen_score_error += 1
            continue
        if not cr.get("pass"):
            skipped_chosen_fail += 1
            continue
        prompt = build_critic_prompt(task)
        chosen_scores = _dim_map(cr)
        threshold = float(task.get("pass_threshold", 75))
        fd = str(task.get("failure_dimension") or "")
        tid = str(task.get("task_id"))

        for mut_id, mut_fn in iter_mutators_for_dimension(fd, allowed_ids=allowed_ids):
            if args.max_pairs_per_task and per_task_pair_count[tid] >= args.max_pairs_per_task:
                break
            out = mut_fn(task, chosen)
            if not out:
                mutator_fail_by_dim[fd] += 1
                continue
            rejected_base, emitted_mut_id, target_dim = out
            rejected = finalize_rejected_below_threshold(
                task, rejected_base, target_dimension=target_dim
            )
            if not rejected:
                skipped_finalize_fail += 1
                continue
            rr = score_task(task, rejected)
            if rr.get("pass"):
                skipped_finalize_fail += 1
                continue

            rec = {
                "schema_version": SCHEMA_VERSION,
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "source_task_id": task.get("task_id"),
                "failure_dimension": fd,
                "source_mode": task.get("source_mode"),
                "edgecase_tags": (task.get("input_context") or {}).get("coverage", {}).get("edgecase_tags")
                or task.get("coverage", {}).get("edgecase_tags"),
                "audit_probes": (task.get("input_context") or {}).get("coverage", {}).get("audit_probes")
                or task.get("coverage", {}).get("audit_probes"),
                "chosen_source": "benchmark_candidate",
                "rejected_mutator_id": emitted_mut_id,
                "target_violation_dimension": target_dim,
                "evaluator_pass_chosen": True,
                "evaluator_pass_rejected": False,
                "evaluator_total_score_chosen": cr.get("total_score"),
                "evaluator_total_score_rejected": rr.get("total_score"),
                "evaluator_scores_chosen": chosen_scores,
                "evaluator_scores_rejected": _dim_map(rr),
                "pass_threshold": threshold,
            }
            pairs.append(rec)
            per_task_pair_count[tid] += 1

    per_dim: Dict[str, int] = defaultdict(int)
    per_src: Dict[str, int] = defaultdict(int)
    for p in pairs:
        per_dim[str(p["failure_dimension"])] += 1
        per_src[str(p["source_mode"])] += 1

    summary = {
        "schema_version": SCHEMA_VERSION,
        "dry_run": args.dry_run,
        "n_pairs": len(pairs),
        "n_skipped_chosen_not_pass": skipped_chosen_fail,
        "n_skipped_chosen_score_error": skipped_chosen_score_error,
        "n_skipped_finalize_or_still_pass": skipped_finalize_fail,
        "pairs_by_failure_dimension": dict(per_dim),
        "pairs_by_source_mode": dict(per_src),
        "mutator_filter": sorted(allowed_ids) if allowed_ids else None,
        "max_pairs_per_task": args.max_pairs_per_task or None,
    }
    print(json.dumps(summary, indent=2))

    if args.dry_run:
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pref_path = args.out_dir / "preferences.jsonl"
    fd, tmp_path = tempfile.mkstemp(dir=args.out_dir, prefix=".preferences.", suffix=".jsonl.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=True) + "\n")
        os.replace(tmp_path, pref_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": _git_head(),
        "scoring_evaluator_sha256": _sha256_file(eval_path),
        "train_jsonl": str(args.train_jsonl.relative_to(REPO_ROOT)),
        "builder_cli": {
            "min_pairs_per_dimension": args.min_pairs_per_dimension,
            "max_pairs_per_task": args.max_pairs_per_task or None,
            "mutators": sorted(allowed_ids) if allowed_ids else "all",
        },
        "n_rows_in_train_jsonl": len(rows),
        "n_tasks_partition_train": len(train_rows),
        "n_skipped_chosen_not_pass": skipped_chosen_fail,
        "n_skipped_chosen_score_error": skipped_chosen_score_error,
        "n_skipped_finalize_or_still_pass": skipped_finalize_fail,
        "n_mutator_failures_by_dimension": dict(mutator_fail_by_dim),
        "n_pairs": len(pairs),
        "pairs_by_failure_dimension": dict(per_dim),
        "pairs_by_source_mode": dict(per_src),
    }
    man_path = args.out_dir / "manifest.json"
    man_text = json.dumps(manifest, indent=2, ensure_ascii=True) + "\n"
    fd_m, tmp_m = tempfile.mkstemp(dir=args.out_dir, prefix=".manifest.", suffix=".json.tmp")
    try:
        with os.fdopen(fd_m, "w", encoding="utf-8") as f:
            f.write(man_text)
        os.replace(tmp_m, man_path)
    except BaseException:
        try:
            os.unlink(tmp_m)
        except OSError:
            pass
        raise

    for dim, need in [
        ("weak_signal_calibration", args.min_pairs_per_dimension),
        ("bench_commitment_safety", args.min_pairs_per_dimension),
        ("tone_marker_safety", args.min_pairs_per_dimension),
        ("multi_system_coordination", args.min_pairs_per_dimension),
        ("non_condescending_gap_framing", args.min_pairs_per_dimension),
    ]:
        got = per_dim.get(dim, 0)
        if got < need:
            print(f"FAIL: {dim} has {got} pairs, need >= {need}")
            raise SystemExit(1)

    print(json.dumps({"wrote": str(pref_path), "manifest": str(args.out_dir / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
