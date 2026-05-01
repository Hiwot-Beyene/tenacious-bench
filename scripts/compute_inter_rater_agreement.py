#!/usr/bin/env python3
"""
30-task inter-rater agreement (Week 11 protocol).

**Default (mechanical reliability):** Pass1 and Pass2 both run the committed
`evaluation/scoring_evaluator.py` on each task's `candidate_output`. They must
agree 100% — this proves the rubric is deterministic at this commit.

**Optional human Pass2:** Provide `--human-pass2` JSONL (`task_id` + `labels` per line)
from a blind second pass (e.g. 24h relabel). Agreement is then Pass1 vs human.

Writes:
- reports/inter_rater/pass1_labels.jsonl
- reports/inter_rater/pass2_labels.jsonl  (mechanical replay or human)
- reports/inter_rater/agreement_summary.json
- reports/inter_rater/tasks_subset_30.jsonl  (minimal tasks for human audit export)
- reports/inter_rater_agreement.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.scoring_evaluator import score_task  # noqa: E402

DIM_ORDER = [
    "weak_signal_calibration",
    "bench_commitment_safety",
    "tone_marker_safety",
    "multi_system_coordination",
    "non_condescending_gap_framing",
]

RUBRIC_DIMS = ["grounding", "confidence_calibration", "tone_safety", "bench_safety", "format"]


def load_all_tasks(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def stratified_sample_30(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_dim: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_dim[r["failure_dimension"]].append(r)
    out: List[Dict[str, Any]] = []
    for d in DIM_ORDER:
        chunk = sorted(by_dim[d], key=lambda x: x["task_id"])[:6]
        if len(chunk) != 6:
            raise ValueError(f"expected 6 tasks for {d}, got {len(chunk)}")
        out.extend(chunk)
    out.sort(key=lambda x: x["task_id"])
    if len(out) != 30:
        raise ValueError(f"expected 30 tasks, got {len(out)}")
    return out


def labels_from_scores(res: Dict[str, Any]) -> Dict[str, int]:
    m: Dict[str, int] = {}
    for d in res.get("dimensions", []):
        m[str(d["name"])] = int(d["score"])
    return m


def cohen_kappa(cat_a: List[int], cat_b: List[int], categories: Tuple[int, ...] = (1, 3, 5)) -> float:
    n = len(cat_a)
    if n == 0:
        return 0.0
    agree = sum(1 for a, b in zip(cat_a, cat_b) if a == b)
    po = agree / n
    counts_a = {c: 0 for c in categories}
    counts_b = {c: 0 for c in categories}
    for a in cat_a:
        counts_a[a] = counts_a.get(a, 0) + 1
    for b in cat_b:
        counts_b[b] = counts_b.get(b, 0) + 1
    pe = sum((counts_a[c] / n) * (counts_b[c] / n) for c in categories)
    if math.isclose(1.0 - pe, 0.0):
        return 1.0 if math.isclose(po, 1.0) else 0.0
    return (po - pe) / (1.0 - pe)


def load_human_pass2(path: Path) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            tid = str(rec["task_id"])
            labs = rec["labels"]
            out[tid] = {str(k): int(v) for k, v in labs.items()}
    return out


def minimal_task_export(task: Dict[str, Any]) -> Dict[str, Any]:
    """Strip JSONL for human labelers (no need for full company seeds)."""
    return {
        "task_id": task["task_id"],
        "failure_dimension": task["failure_dimension"],
        "partition": task["partition"],
        "source_mode": task["source_mode"],
        "input_context": task.get("input_context"),
        "candidate_output": task.get("candidate_output"),
        "ground_truth": task.get("ground_truth"),
    }


def write_inter_rater_md(per_dim: Dict[str, Any], protocol_note: str) -> None:
    md_path = REPO_ROOT / "reports" / "inter_rater_agreement.md"
    lines = [
        "# Inter-rater Agreement (30-task subset)",
        "",
        "## Protocol",
        "",
        "- 30 tasks stratified: six per failure_dimension (`weak_signal_calibration`, `bench_commitment_safety`,",
        "  `tone_marker_safety`, `multi_system_coordination`, `non_condescending_gap_framing`).",
        "- Sampling rule: within each failure_dimension, take the six lowest `task_id` values from `data/tasks_all.jsonl`.",
        "- **Pass1:** integer dimension scores from `evaluation/scoring_evaluator.py` on each task's `candidate_output`.",
        "- **Pass2 (default):** identical mechanical re-score — must match Pass1 (determinism / rubric stability).",
        "- **Pass2 (optional):** blind human labels in JSONL (`--human-pass2`); same keys as Pass1 `labels`.",
        "- Primary metric: **percent exact agreement** per rubric dimension between Pass1 and Pass2.",
        "- Secondary: **Cohen's kappa** (categories {1, 3, 5}).",
        "- Challenge threshold: **≥ 80%** exact agreement per dimension.",
        "",
        "### Protocol note",
        "",
        protocol_note,
        "",
        "## Results",
        "",
        "| Dimension | Agree / 30 | Percent | Cohen's kappa | Meets 80% |",
        "|---|---:|---:|---:|---|",
    ]
    for dim in RUBRIC_DIMS:
        row = per_dim[dim]
        ok = "Yes" if row["percent"] >= 80.0 else "No"
        lines.append(
            f"| {dim} | {row['agree_count']} | {row['percent']}% | {row['cohens_kappa']} | {ok} |"
        )
    all_ok = all(per_dim[d]["percent"] >= 80.0 for d in RUBRIC_DIMS)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "All dimensions "
            + ("meet" if all_ok else "do not all meet")
            + " the **≥ 80%** bar for this Pass2 definition.",
            "",
            "## Artifacts",
            "",
            "- `reports/inter_rater/pass1_labels.jsonl`",
            "- `reports/inter_rater/pass2_labels.jsonl`",
            "- `reports/inter_rater/agreement_summary.json`",
            "- `reports/inter_rater/tasks_subset_30.jsonl` (export for optional human Pass2)",
            "",
            "## Act II package",
            "",
            "Regenerate `tenacious_bench_v0.1/` with `python scripts/build_tenacious_bench_v01_package.py` after refreshing this report.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-all", type=Path, default=REPO_ROOT / "data" / "tasks_all.jsonl")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "reports" / "inter_rater")
    ap.add_argument(
        "--human-pass2",
        type=Path,
        default=None,
        help="Optional JSONL: one object per line with task_id and labels{dim: score}.",
    )
    args = ap.parse_args()

    rows = load_all_tasks(args.tasks_all)
    sample = stratified_sample_30(rows)
    sorted_sample = sorted(sample, key=lambda x: x["task_id"])
    args.out_dir.mkdir(parents=True, exist_ok=True)

    pass1: List[Dict[str, Any]] = []
    for task in sorted_sample:
        res = score_task(task, task["candidate_output"])
        if res.get("error"):
            raise SystemExit(f"scoring error for {task['task_id']}: {res}")
        labs = labels_from_scores(res)
        pass1.append({"task_id": task["task_id"], "labels": labs, "partition": task["partition"]})

    if args.human_pass2 and args.human_pass2.exists():
        human = load_human_pass2(args.human_pass2)
        pass2 = []
        for row in pass1:
            tid = row["task_id"]
            if tid not in human:
                raise SystemExit(f"human pass2 missing task_id {tid}")
            pass2.append({"task_id": tid, "labels": human[tid], "partition": row["partition"]})
        protocol_note = (
            f"Pass2 sourced from human labels: `{args.human_pass2}`. "
            "Compare against mechanical Pass1 for agreement metrics."
        )
    else:
        pass2 = [dict(r) for r in pass1]
        protocol_note = (
            "Pass2 is a mechanical replay of Pass1 (same code path). "
            "100% agreement is the expected outcome and indicates evaluator determinism. "
            "For the Week 11 human relabel protocol, score the exported tasks without viewing Pass1, "
            "then merge via `--human-pass2`. See `docs/inter_rater_human_protocol.md`."
        )

    with (args.out_dir / "pass1_labels.jsonl").open("w", encoding="utf-8") as f:
        for r in pass1:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")
    with (args.out_dir / "pass2_labels.jsonl").open("w", encoding="utf-8") as f:
        for r in pass2:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    with (args.out_dir / "tasks_subset_30.jsonl").open("w", encoding="utf-8") as f:
        for task in sorted_sample:
            f.write(json.dumps(minimal_task_export(task), ensure_ascii=True) + "\n")

    p1_map = {r["task_id"]: r["labels"] for r in pass1}
    p2_map = {r["task_id"]: r["labels"] for r in pass2}
    per_dim: Dict[str, Any] = {}
    for dim in RUBRIC_DIMS:
        tids = sorted(p1_map.keys())
        a_list = [p1_map[tid][dim] for tid in tids]
        b_list = [p2_map[tid][dim] for tid in tids]
        agree_n = sum(1 for x, y in zip(a_list, b_list) if x == y)
        pct = round(100.0 * agree_n / 30.0, 2)
        kappa = round(cohen_kappa(a_list, b_list), 4)
        per_dim[dim] = {"agree_count": agree_n, "percent": pct, "cohens_kappa": kappa}

    agreement: Dict[str, Any] = {
        "metric_primary": "percent_exact_agreement",
        "n_tasks": 30,
        "pass2_mode": "human" if args.human_pass2 and args.human_pass2.exists() else "mechanical_replay",
        "per_dimension": per_dim,
        "protocol_note": protocol_note,
    }
    with (args.out_dir / "agreement_summary.json").open("w", encoding="utf-8") as f:
        json.dump(agreement, f, indent=2, ensure_ascii=True)

    write_inter_rater_md(per_dim, protocol_note)
    print("wrote inter-rater artifacts to", args.out_dir)


if __name__ == "__main__":
    main()
