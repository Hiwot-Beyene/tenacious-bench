#!/usr/bin/env python3
"""
Build Tenacious-Bench v0.1 JSONL from real company seeds (Crunchbase ODM + workspaces).

This is the single canonical corpus builder. It replaces ad-hoc placeholder generators:
tasks reference actual `name` / `domain` / firmographics from `data/company_seeds.json`
(produced on first run from conversion-engine data).

Outputs:
  data/tasks_{train,dev,heldout}.jsonl, data/tasks_all.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.anchor_packs import load_bench_summary_json  # noqa: E402
from bench_corpus.constants import CELL_COUNTS  # noqa: E402
from bench_corpus.scenarios import build_task_payload  # noqa: E402
from bench_corpus.seeds import ensure_company_seeds, load_trace_anchors, default_paths  # noqa: E402


def materialize(
    out_dir: Path,
    companies: List[Dict[str, Any]],
    traces: List[Tuple[str, str]],
    capacity_snapshot: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    by_partition: Dict[str, List[Dict[str, Any]]] = {"train": [], "dev": [], "heldout": []}
    fd_slot: Dict[str, int] = defaultdict(int)
    trace_i = 0
    seq = 0

    for failure_dimension, part_map in CELL_COUNTS.items():
        for partition, src_map in part_map.items():
            for source_mode, count in src_map.items():
                for _ in range(count):
                    seq += 1
                    li = fd_slot[failure_dimension]
                    fd_slot[failure_dimension] += 1

                    company = companies[(seq - 1) % len(companies)]
                    trace: Tuple[str, str] | None = None
                    if source_mode == "trace_derived" and traces:
                        trace = traces[trace_i % len(traces)]
                        trace_i += 1

                    route = (
                        "qwen/qwen3-next-80b-a3b-instruct"
                        if seq % 2 == 0
                        else "deepseek/deepseek-chat"
                    )
                    row = build_task_payload(
                        seq=seq,
                        failure_dimension=failure_dimension,
                        partition=partition,
                        source_mode=source_mode,
                        company=company,
                        local_idx=li,
                        trace=trace,
                        synthesis_route=route,
                        capacity_snapshot=capacity_snapshot,
                    )
                    by_partition[partition].append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    for part, rows in by_partition.items():
        path = out_dir / f"tasks_{part}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")

    all_rows: List[Dict[str, Any]] = []
    for part in ("train", "dev", "heldout"):
        all_rows.extend(by_partition[part])
    all_path = out_dir / "tasks_all.jsonl"
    with all_path.open("w", encoding="utf-8") as f:
        for r in sorted(all_rows, key=lambda x: x["task_id"]):
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    return all_rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Build v0.1 corpus from real company seeds.")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data")
    ap.add_argument(
        "--refresh-seeds",
        action="store_true",
        help="Rebuild data/company_seeds.json from Crunchbase + workspaces.",
    )
    args = ap.parse_args()

    paths = default_paths(REPO_ROOT)
    companies = ensure_company_seeds(REPO_ROOT, write=args.refresh_seeds)
    traces = load_trace_anchors(paths["traces"])
    monorepo = REPO_ROOT.parent
    bench_path = (
        monorepo / "conversion-engine" / "tenacious_sales_data" / "seed" / "bench_summary.json"
    )
    capacity_snapshot = load_bench_summary_json(bench_path)
    if capacity_snapshot is None:
        print(
            f"warning: missing or unreadable bench snapshot at {bench_path}; "
            "named capacity placeholders default to 0 and snapshot_as_of=unavailable.",
            file=sys.stderr,
        )

    rows = materialize(args.out_dir, companies, traces, capacity_snapshot)
    print(f"wrote {len(rows)} tasks to {args.out_dir} using {len(companies)} company seeds")


if __name__ == "__main__":
    main()
