#!/usr/bin/env python3
"""Materialized JSONL must carry coverage metadata and satisfy self-score baseline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.audit_probe_registry import EXPECTED_AUDIT_PROBES  # noqa: E402
from evaluation.scoring_evaluator import score_numeric  # noqa: E402


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-all", type=Path, default=REPO_ROOT / "data" / "tasks_all.jsonl")
    ap.add_argument("--pass-threshold", type=float, default=75.0)
    ap.add_argument(
        "--allow-missing-snapshot",
        action="store_true",
        help="Do not require internal_capacity_snapshot (offline / legacy builds only).",
    )
    args = ap.parse_args()

    rows = list(iter_jsonl(args.tasks_all))
    errs: List[str] = []
    probes_seen: Set[str] = set()

    for r in rows:
        tid = r.get("task_id")
        ic = r.get("input_context") or {}
        cov = ic.get("coverage") or r.get("coverage") or {}
        tags = cov.get("edgecase_tags") if isinstance(cov, dict) else None
        probes = cov.get("audit_probes") if isinstance(cov, dict) else None

        if not isinstance(tags, list) or not tags:
            errs.append(f"{tid}: missing coverage.edgecase_tags")
        if not isinstance(probes, list) or not probes:
            errs.append(f"{tid}: missing coverage.audit_probes")
        else:
            for p in probes:
                probes_seen.add(str(p))

        if not args.allow_missing_snapshot and not isinstance(ic.get("internal_capacity_snapshot"), dict):
            errs.append(f"{tid}: missing input_context.internal_capacity_snapshot")

        gt = r.get("ground_truth") or {}
        anchors = gt.get("grounding_anchors")
        if isinstance(anchors, list) and anchors:
            out = (r.get("candidate_output") or "").lower()
            for a in anchors:
                if str(a).lower() not in out:
                    errs.append(f"{tid}: grounding_anchor not in candidate_output: {a!r}")

        cand = r.get("candidate_output") or ""
        sc = score_numeric(r, cand)
        if sc < args.pass_threshold:
            errs.append(f"{tid}: self-score {sc} < {args.pass_threshold}")

    missing_probes = sorted(EXPECTED_AUDIT_PROBES - probes_seen)
    if missing_probes:
        errs.append(
            "materialized corpus never emits these audit probes in task coverage: " + str(missing_probes)
        )

    if errs:
        print("MATERIALIZED TASK COVERAGE FAIL:\n" + "\n".join(errs[:60]))
        if len(errs) > 60:
            print(f"... and {len(errs) - 60} more")
        raise SystemExit(1)

    print(
        f"materialized task coverage OK: {len(rows)} tasks, "
        f"all score >= {args.pass_threshold} on candidate_output, "
        f"{len(probes_seen)} unique audit probes present",
    )


if __name__ == "__main__":
    main()
