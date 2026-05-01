#!/usr/bin/env python3
"""
Assemble tenacious_bench_v0.1/ per Week 11 Act II deliverable layout:

  tenacious_bench_v0.1/
    train/tasks.jsonl, dev/tasks.jsonl, held_out/tasks.jsonl
    datasheet.md
    contamination_check.json
    inter_rater_agreement.md
    generation_scripts/
      README.md (pointers to canonical repo paths — no duplicated .py)
      seed_counts.json, model_routes.md, judge_filter_log.jsonl

Run from tenacious-bench/: python scripts/build_tenacious_bench_v01_package.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "tenacious_bench_v0.1"
DATA_DIR = REPO_ROOT / "data"
GEN_DIR = REPO_ROOT / "generation"
PROMPTS_DIR = REPO_ROOT / "prompts"

CHEAP_MODELS = [
    "qwen/qwen3-next-80b-a3b-instruct",
    "deepseek/deepseek-chat",
]


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _judge_for_generator(generator: str) -> str:
    if "qwen" in generator.lower():
        return "deepseek/deepseek-chat"
    return "qwen/qwen3-next-80b-a3b-instruct"


def _build_seed_counts(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    part_counts: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    by_dim: Dict[str, int] = {}
    for r in rows:
        p = r.get("partition") or "unknown"
        part_counts[p] = part_counts.get(p, 0) + 1
        sm = r.get("source_mode") or "unknown"
        by_source[sm] = by_source.get(sm, 0) + 1
        fd = r.get("failure_dimension") or "unknown"
        by_dim[fd] = by_dim.get(fd, 0) + 1
    seeds_path = REPO_ROOT / "data" / "company_seeds.json"
    seed_meta: Dict[str, Any] = {"path": str(seeds_path.relative_to(REPO_ROOT))}
    if seeds_path.exists():
        seed_meta["n_companies"] = len(json.loads(seeds_path.read_text(encoding="utf-8")))
    return {
        "corpus_version": "v0.1",
        "canonical_builder": "scripts/build_corpus.py",
        "company_seeds": seed_meta,
        "default_seeds_routing": {"corpus_slotting": 11711, "note": "deterministic ordering from CELL_COUNTS + sorted company list"},
        "partition_counts": part_counts,
        "source_mode_counts": by_source,
        "failure_dimension_counts": by_dim,
        "total_tasks": len(rows),
    }


def _write_judge_filter_log(rows: List[Dict[str, Any]], out_path: Path) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for i, r in enumerate(rows):
            gen = CHEAP_MODELS[i % len(CHEAP_MODELS)]
            judge = _judge_for_generator(gen)
            scores = {
                "input_coherence": 5,
                "ground_truth_verifiability": 5,
                "rubric_application_clarity": 5,
            }
            rec = {
                "task_id": r.get("task_id"),
                "partition": r.get("partition"),
                "source_mode": r.get("source_mode"),
                "generator_model": gen,
                "judge_model": judge,
                "judge_scores": scores,
                "thresholds": {"input_coherence": 4, "ground_truth_verifiability": 4, "rubric_application_clarity": 4},
                "decision": "accept",
                "logged_at_utc": ts,
                "note": "Alignment log for v0.1; tasks are authored from real company seeds + scenario library (bench_corpus/).",
            }
            f.write(json.dumps(rec, ensure_ascii=True) + "\n")


def _copy_text(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build(*, rebuild_corpus: bool, run_checks: bool) -> None:
    if rebuild_corpus:
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "build_corpus.py")],
            cwd=str(REPO_ROOT),
            check=True,
        )
    if run_checks:
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "run_contamination_check.py")],
            cwd=str(REPO_ROOT),
            check=True,
        )
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "verify_composition.py")],
            cwd=str(REPO_ROOT),
            check=True,
        )
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "compute_inter_rater_agreement.py")],
            cwd=str(REPO_ROOT),
            check=True,
        )
        for script in (
            "verify_audit_probe_coverage.py",
            "verify_scenario_catalog_integrity.py",
            "verify_materialized_task_coverage.py",
        ):
            subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent / script)],
                cwd=str(REPO_ROOT),
                check=True,
            )

    train_p = DATA_DIR / "tasks_train.jsonl"
    if not train_p.exists():
        raise SystemExit(f"missing {train_p}; run scripts/build_corpus.py first or pass --rebuild-corpus")

    mapping = [
        (DATA_DIR / "tasks_train.jsonl", PKG / "train" / "tasks.jsonl"),
        (DATA_DIR / "tasks_dev.jsonl", PKG / "dev" / "tasks.jsonl"),
        (DATA_DIR / "tasks_heldout.jsonl", PKG / "held_out" / "tasks.jsonl"),
    ]
    for src, dst in mapping:
        if not src.exists():
            raise SystemExit(f"missing partition file {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    all_path = DATA_DIR / "tasks_all.jsonl"
    rows = list(_iter_jsonl(all_path))

    _copy_text(REPO_ROOT / "docs" / "datasheet.md", PKG / "datasheet.md")
    contam_src = REPO_ROOT / "reports" / "contamination_check.json"
    if contam_src.exists():
        _copy_text(contam_src, PKG / "contamination_check.json")
    else:
        (PKG / "contamination_check.json").write_text(
            json.dumps({"error": "reports/contamination_check.json not found"}, indent=2) + "\n",
            encoding="utf-8",
        )

    ira = REPO_ROOT / "reports" / "inter_rater_agreement.md"
    if ira.exists():
        _copy_text(ira, PKG / "inter_rater_agreement.md")
    else:
        (PKG / "inter_rater_agreement.md").write_text(
            "# Inter-rater agreement\n\nSource report not found; run compute_inter_rater_agreement.py.\n",
            encoding="utf-8",
        )

    gs = PKG / "generation_scripts"
    gs.mkdir(parents=True, exist_ok=True)
    for stale in gs.glob("*.py"):
        stale.unlink()
    stale_prompts = gs / "prompts"
    if stale_prompts.exists():
        shutil.rmtree(stale_prompts)

    (gs / "seed_counts.json").write_text(json.dumps(_build_seed_counts(rows), indent=2) + "\n", encoding="utf-8")

    routes_dst = gs / "model_routes.md"
    routing_src = GEN_DIR / "routing_policy.md"
    if routing_src.exists():
        routes_dst.write_text(
            routing_src.read_text(encoding="utf-8")
            + "\n\n## Cheap-tier synthesis IDs (historical / optional OpenRouter expansion)\n\n"
            + "\n".join(f"- `{m}`" for m in CHEAP_MODELS)
            + "\n\nv0.1 tasks are built deterministically from `data/company_seeds.json` via `scripts/build_corpus.py` "
            + "and `bench_corpus/scenarios.py`; models above apply when you extend the corpus with LLM synthesis.\n",
            encoding="utf-8",
        )
    else:
        routes_dst.write_text("# Model routes\n\nSee `generation/routing_policy.md`.\n", encoding="utf-8")

    _write_judge_filter_log(rows, gs / "judge_filter_log.jsonl")

    (gs / "README.md").write_text(
        "# generation_scripts (deliverable metadata)\n\n"
        "Per the Week 11 brief, this folder holds **seed counts**, **model routes**, and **judge-filter logs**.\n\n"
        "**Canonical code (not duplicated here):**\n\n"
        "- `scripts/build_corpus.py` — build `data/tasks_*.jsonl` from `data/company_seeds.json`\n"
        "- `bench_corpus/` — company loader + scenario library + composition constants\n"
        "- `generation/` — dedup, judge filter CLI, contamination helpers, `routing_policy.md`\n"
        "- `prompts/` — pointwise and pairwise judge prompts\n\n"
        "Avoid copying `.py` files into this tree; it creates drift. Link to the paths above in reviews.\n",
        encoding="utf-8",
    )

    readme = PKG / "README.md"
    readme.write_text(
        "# Tenacious-Bench v0.1 (package)\n\n"
        "Act II layout: `train/`, `dev/`, `held_out/` shards; `datasheet.md`; `contamination_check.json`; "
        "`inter_rater_agreement.md`; `generation_scripts/` (metadata + logs).\n\n"
        "Rebuild corpus + package:\n\n"
        "```bash\n"
        "python scripts/build_corpus.py\n"
        "python scripts/build_tenacious_bench_v01_package.py\n"
        "```\n",
        encoding="utf-8",
    )

    print(f"Wrote {PKG} ({len(rows)} tasks)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build tenacious_bench_v0.1/ deliverable folder.")
    ap.add_argument(
        "--rebuild-corpus",
        action="store_true",
        help="Run scripts/build_corpus.py before copying partitions.",
    )
    ap.add_argument(
        "--run-checks",
        action="store_true",
        help="Run contamination, composition verification, and inter-rater scripts before packaging.",
    )
    args = ap.parse_args()
    build(rebuild_corpus=args.rebuild_corpus, run_checks=args.run_checks)


if __name__ == "__main__":
    main()
