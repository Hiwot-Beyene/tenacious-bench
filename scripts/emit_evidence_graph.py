#!/usr/bin/env python3
"""
Merge Act V publication URLs with committed evidence artifacts into reports/evidence_graph.json.

Reads:
  reports/act_v_urls.json          — URLs you fill after HF / blog / community posts
  reports/ablation_results.json    — optional; headline metrics
  training_data/manifest.json      — preference corpus stats
  outputs/*/training_meta.json     — optional; best-effort first match

Usage:
  cd tenacious-bench
  uv run python scripts/emit_evidence_graph.py
  uv run python scripts/emit_evidence_graph.py --training-meta outputs/preference_lora_day5/training_meta.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return _read_json(path)
    except (json.JSONDecodeError, OSError):
        return None


def _find_training_meta(preferred: Optional[Path]) -> Optional[Path]:
    if preferred and preferred.exists():
        return preferred
    candidates = sorted(
        REPO_ROOT.glob("outputs/**/training_meta.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _headline_from_ablation(ab: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "n_pairs_scored": ab.get("n_pairs") or ab.get("n_pairs_input"),
        "comparisons_run": ab.get("comparisons_run"),
    }
    da = ab.get("delta_a_trained_vs_baseline")
    if isinstance(da, dict) and "mean_delta_accuracy" in da:
        out["delta_a"] = {
            "mean_delta_accuracy": da.get("mean_delta_accuracy"),
            "ci95_low": da.get("ci95_low"),
            "ci95_high": da.get("ci95_high"),
            "p_value_two_sided": da.get("p_value_paired_bootstrap_two_sided"),
        }
    db = ab.get("delta_b_trained_vs_prompt_only")
    if isinstance(db, dict) and "mean_delta_accuracy" in db:
        out["delta_b"] = {
            "mean_delta_accuracy": db.get("mean_delta_accuracy"),
            "ci95_low": db.get("ci95_low"),
            "ci95_high": db.get("ci95_high"),
            "p_value_two_sided": db.get("p_value_paired_bootstrap_two_sided"),
        }
    dc = ab.get("delta_c_tau2_retail")
    if isinstance(dc, dict):
        out["delta_c_tau2_informational"] = {
            "week10_score_on_file": dc.get("week10_score_on_file"),
        }
    cp = ab.get("cost_pareto")
    if isinstance(cp, dict):
        out["cost_pareto_summary"] = cp
    acc = ab.get("accuracies")
    if isinstance(acc, dict):
        out["accuracies"] = acc
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build reports/evidence_graph.json for Act V.")
    ap.add_argument(
        "--urls",
        type=Path,
        default=REPO_ROOT / "reports" / "act_v_urls.json",
    )
    ap.add_argument("--ablation", type=Path, default=REPO_ROOT / "reports" / "ablation_results.json")
    ap.add_argument("--manifest", type=Path, default=REPO_ROOT / "training_data" / "manifest.json")
    ap.add_argument("--training-meta", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "reports" / "evidence_graph.json")
    args = ap.parse_args()

    if not args.urls.exists():
        raise SystemExit(
            f"missing {args.urls}; create it from reports/act_v_urls.json (template is committed with null URLs)"
        )

    urls_raw = _read_json(args.urls)
    urls_public = {k: v for k, v in urls_raw.items() if not str(k).startswith("_")}

    manifest = _safe_read(args.manifest)
    ablation = _safe_read(args.ablation)
    meta_path = _find_training_meta(args.training_meta)
    training_meta = _safe_read(meta_path) if meta_path else None

    evidence_paths = {
        "audit_memo": "docs/audit_memo.md",
        "methodology": "docs/methodology.md",
        "methodology_rationale_path_b": "docs/methodology_rationale.md",
        "datasheet": "docs/datasheet.md",
        "scoring_evaluator": "evaluation/scoring_evaluator.py",
        "tasks_all_jsonl": "data/tasks_all.jsonl",
        "preferences_jsonl": "training_data/preferences.jsonl",
        "contamination_report": "reports/contamination_check.json",
        "inter_rater": "reports/inter_rater_agreement.md",
        "composition_crosstab": "reports/composition_crosstab.md",
        "model_card": "reports/model_card.md",
        "ceo_cfo_memo_pdf": "memo.pdf",
        "training_run_log": "reports/training_run.log",
        "ablation_results": "reports/ablation_results.json",
        "held_out_traces": "reports/held_out_traces.jsonl",
    }

    graph: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "challenge": "TRP1 Week 11 — Tenacious-Bench",
        "repository_root_relative": ".",
        "act_v_publication_urls": urls_public,
        "evidence_artifacts": evidence_paths,
        "preference_corpus_manifest": manifest,
        "training_run_meta": training_meta,
        "training_meta_path_resolved": str(meta_path.relative_to(REPO_ROOT)) if meta_path else None,
    }

    if ablation:
        graph["held_out_ablation"] = {
            "source_file": str(args.ablation.relative_to(REPO_ROOT)),
            "generated_at_utc": ablation.get("generated_at_utc"),
            "harness": ablation.get("harness"),
            "headline_metrics": _headline_from_ablation(ablation),
        }
    else:
        graph["held_out_ablation"] = None

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(graph, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(args.out), "training_meta_used": graph["training_meta_path_resolved"]}, indent=2))


if __name__ == "__main__":
    main()
