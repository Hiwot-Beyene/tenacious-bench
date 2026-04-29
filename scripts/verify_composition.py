#!/usr/bin/env python3
"""
Verify materialized corpus matches datasheet marginals and emit cross-tab reports.

Reads data/tasks_train.jsonl, data/tasks_dev.jsonl, data/tasks_heldout.jsonl
(or --data-dir glob).

Exit code non-zero on mismatch.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

TARGET_PARTITION = {"train": 120, "dev": 72, "heldout": 48}
TARGET_SOURCE = {
    "trace_derived": 72,
    "programmatic": 72,
    "multi_llm_synthesis": 60,
    "hand_authored_adversarial": 36,
}
TARGET_DIMENSION = {
    "weak_signal_calibration": 52,
    "bench_commitment_safety": 44,
    "tone_marker_safety": 50,
    "multi_system_coordination": 38,
    "non_condescending_gap_framing": 56,
}

DIM_ORDER = list(TARGET_DIMENSION.keys())
PART_ORDER = ["train", "dev", "heldout"]
SRC_ORDER = list(TARGET_SOURCE.keys())


def iter_tasks(paths: List[Path]) -> Iterable[Dict[str, Any]]:
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


def build_crosstab(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    cell: DefaultDict[str, DefaultDict[str, DefaultDict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    for r in rows:
        d = r["failure_dimension"]
        p = r["partition"]
        s = r["source_mode"]
        cell[d][p][s] += 1

    out_cells: Dict[str, Any] = {}
    for d in DIM_ORDER:
        for p in PART_ORDER:
            key = f"{d}|{p}"
            out_cells[key] = {src: cell[d][p][src] for src in SRC_ORDER}
    return {"cells": out_cells, "raw": {d: dict(cell[d]) for d in cell}}


def margins(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    part: Dict[str, int] = defaultdict(int)
    src: Dict[str, int] = defaultdict(int)
    dim: Dict[str, int] = defaultdict(int)
    for r in rows:
        part[r["partition"]] += 1
        src[r["source_mode"]] += 1
        dim[r["failure_dimension"]] += 1
    return dict(part), dict(src), dict(dim)


def _assert_targets(name: str, actual: Dict[str, int], target: Dict[str, int]) -> List[str]:
    errs: List[str] = []
    for k, tv in target.items():
        av = actual.get(k, 0)
        if av != tv:
            errs.append(f"{name} {k}: expected {tv}, got {av}")
    for k in actual:
        if k not in target:
            errs.append(f"{name} unexpected key {k}={actual[k]}")
    return errs


def markdown_table(rows: List[Dict[str, Any]]) -> str:
    cell: DefaultDict[str, DefaultDict[str, DefaultDict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    for r in rows:
        cell[r["failure_dimension"]][r["partition"]][r["source_mode"]] += 1

    lines: List[str] = []
    header = (
        "| failure_dimension | partition | trace_derived | programmatic | "
        "multi_llm_synthesis | hand_authored_adversarial | row_total |"
    )
    sep = "|---|---|---:|---:|---:|---:|---:|"
    lines.extend([header, sep])
    col_totals = {s: 0 for s in SRC_ORDER}
    for d in DIM_ORDER:
        for p in PART_ORDER:
            vals = [cell[d][p][s] for s in SRC_ORDER]
            rt = sum(vals)
            for s, v in zip(SRC_ORDER, vals):
                col_totals[s] += v
            lines.append(
                f"| {d} | {p} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | {rt} |"
            )
    ct = sum(col_totals[s] for s in SRC_ORDER)
    lines.append(
        "| **column_totals** | **all** | "
        f"{col_totals['trace_derived']} | {col_totals['programmatic']} | "
        f"{col_totals['multi_llm_synthesis']} | {col_totals['hand_authored_adversarial']} | {ct} |"
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data")
    ap.add_argument("--reports-dir", type=Path, default=REPO_ROOT / "reports")
    args = ap.parse_args()

    paths = [
        args.data_dir / "tasks_train.jsonl",
        args.data_dir / "tasks_dev.jsonl",
        args.data_dir / "tasks_heldout.jsonl",
    ]
    for p in paths:
        if not p.exists():
            raise SystemExit(f"missing {p}; run scripts/materialize_corpus.py first")

    rows = list(iter_tasks(paths))
    part_m, src_m, dim_m = margins(rows)
    errs: List[str] = []
    errs.extend(_assert_targets("partition", part_m, TARGET_PARTITION))
    errs.extend(_assert_targets("source_mode", src_m, TARGET_SOURCE))
    errs.extend(_assert_targets("failure_dimension", dim_m, TARGET_DIMENSION))
    if len(rows) != 240:
        errs.append(f"total count expected 240, got {len(rows)}")

    ctab = build_crosstab(rows)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    md_path = args.reports_dir / "composition_crosstab.md"
    summary = {
        "total_tasks": len(rows),
        "partition_margins": part_m,
        "source_mode_margins": src_m,
        "failure_dimension_margins": dim_m,
        "targets": {
            "partition": TARGET_PARTITION,
            "source_mode": TARGET_SOURCE,
            "failure_dimension": TARGET_DIMENSION,
        },
        "deviation": "none" if not errs else "; ".join(errs),
        "crosstab_cells": ctab["cells"],
    }
    json_path = args.reports_dir / "composition_actual.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=True)

    ok = not errs
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Tenacious-Bench v0.1 composition (materialized)\n\n")
        f.write("Generated by `scripts/verify_composition.py` from partitioned JSONL.\n\n")
        f.write("## Margins vs targets\n\n")
        f.write("| Check | Status |\n|---|---|\n")
        f.write(f"| Total tasks | {'PASS' if len(rows) == 240 else 'FAIL'} ({len(rows)} vs 240) |\n")
        f.write(f"| Partition margins | {'PASS' if not _assert_targets('partition', part_m, TARGET_PARTITION) else 'FAIL'} |\n")
        f.write(f"| Source-mode margins | {'PASS' if not _assert_targets('source_mode', src_m, TARGET_SOURCE) else 'FAIL'} |\n")
        f.write(f"| Failure-dimension margins | {'PASS' if not _assert_targets('failure_dimension', dim_m, TARGET_DIMENSION) else 'FAIL'} |\n")
        f.write(f"| **Overall** | **{'PASS' if ok else 'FAIL'}** |\n\n")
        f.write("## Integrated cross-tab (dimension x partition x source_mode)\n\n")
        f.write(markdown_table(rows))
        f.write("\n")

    if errs:
        print("COMPOSITION FAIL:\n" + "\n".join(errs))
        raise SystemExit(1)
    print("composition OK:", json_path)


if __name__ == "__main__":
    main()
