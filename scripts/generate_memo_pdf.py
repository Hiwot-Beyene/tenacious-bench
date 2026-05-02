#!/usr/bin/env python3
"""
Build memo.pdf (Week 11 final submission): two-page CEO/CFO memo per challenge brief.

Page 1: decision summary, Delta A with CI, Delta B, cost, deployment recommendation.
Page 2: skeptic's appendix (gaps in v0.1, signal lossiness, unresolved training issue, kill-switch).

Reads metrics from reports/ablation_results.json when a full ablation is present; otherwise uses
explicit placeholders so you can still generate a PDF and re-run after sealed ablation.

Usage:
  cd tenacious-bench
  uv sync --extra pdf
  uv run python scripts/generate_memo_pdf.py
  uv run python scripts/generate_memo_pdf.py --out reports/memo.pdf
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _fmt_delta(block: Optional[Dict[str, Any]]) -> str:
    if not block or "mean_delta_accuracy" not in block:
        return (
            "[Pending: run `uv run python scripts/run_sealed_ablation.py` and re-run this script.]"
        )
    m = block["mean_delta_accuracy"]
    lo = block.get("ci95_low")
    hi = block.get("ci95_high")
    p1 = block.get("p_value_paired_bootstrap_one_sided")
    p2 = block.get("p_value_paired_bootstrap_two_sided")
    ps = f"p(one-sided)={p1:.4f}" if isinstance(p1, (int, float)) else ""
    if isinstance(p2, (int, float)):
        ps += f", p(two-sided)={p2:.4f}"
    return (
        f"Mean Delta accuracy {m:+.4f}; 95% bootstrap CI [{lo}, {hi}]. {ps}. "
        f"(Paired bootstrap on held-out preference slice; see reports/ablation_results.json.)"
    )


def _fmt_cost(ab: Optional[Dict[str, Any]]) -> str:
    if not ab:
        return "[See reports/ablation_results.json cost_pareto after full ablation.]"
    cp = ab.get("cost_pareto")
    if not isinstance(cp, dict):
        return "[Cost-Pareto not in current ablation file.]"
    lines = []
    for k in ("baseline", "trained", "prompt_only"):
        v = cp.get(k)
        if isinstance(v, dict) and "ms_per_pair_mean" in v:
            lines.append(
                f"{k}: ~{v['ms_per_pair_mean']:.0f} ms/pair mean; "
                f"completion tokens mean ~{v.get('completion_tokens_mean', 0):.1f}."
            )
    return " ".join(lines) if lines else "[cost_pareto missing]"


def _extract_ablation_summary(ab: Optional[Dict[str, Any]]) -> Tuple[str, str, str, str]:
    if not ab:
        return (
            _fmt_delta(None),
            _fmt_delta(None),
            _fmt_cost(None),
            "Deploy with caveat: rerun sealed ablation for headline numbers before production gate.",
        )
    da = ab.get("delta_a_trained_vs_baseline")
    db = ab.get("delta_b_trained_vs_prompt_only")
    if not isinstance(da, dict) or "mean_delta_accuracy" not in da:
        return (
            _fmt_delta(None),
            _fmt_delta(None),
            _fmt_cost(ab),
            "Deploy with caveat: inconclusive lift until Delta A/B computed on full held-out run.",
        )
    rec = (
        "Do not deploy as a sole gate: Delta A does not separate from zero at p<0.05 on current slice; "
        "use as an auxiliary signal and expand preference data before relying on it for rejection."
    )
    m = float(da["mean_delta_accuracy"])
    p2 = da.get("p_value_paired_bootstrap_two_sided")
    if isinstance(p2, (int, float)) and p2 < 0.05 and m > 0:
        rec = (
            "Deploy with monitoring: positive Delta A with two-sided p<0.05; still validate task-level "
            "rubric outcomes and cost-Pareto before full rollout."
        )
    return _fmt_delta(da if isinstance(da, dict) else None), _fmt_delta(
        db if isinstance(db, dict) else None
    ), _fmt_cost(ab), rec


def main() -> None:
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError as e:
        raise SystemExit(
            "Install PDF extra: cd tenacious-bench && uv sync --extra pdf\n" + str(e)
        ) from e

    ap = argparse.ArgumentParser(description="Generate Week 11 memo.pdf")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "memo.pdf")
    ap.add_argument(
        "--ablation",
        type=Path,
        default=REPO_ROOT / "reports" / "ablation_results.json",
    )
    args = ap.parse_args()

    ab = _read_json(args.ablation)
    d1, d2, cost, recommendation = _extract_ablation_summary(ab)

    today = date.today().isoformat()

    lines_p1 = [
        "MEMORANDUM",
        "",
        "To: CEO, CFO, Engineering leadership",
        "From: Hiwot Beyene (Tenacious-Bench / Week 11)",
        f"Date: {today}",
        "Subject: Tenacious-Bench v0.1 + Path B critic - decision and deployment",
        "",
        "Executive summary (three sentences)",
        "We shipped a reproducible Path B pipeline (DPO + LoRA preference critic) and a 240-task ",
        "Tenacious-Bench v0.1 corpus with mechanical scoring, datasheet, and public Hub artifacts. ",
        "Held-out preference ablations are the primary Week 11 lift metric; cost and latency are ",
        "tracked for Pareto decisions. This memo states the numeric headline, an honest Delta B, ",
        "and a deployment recommendation with a kill-switch on page 2.",
        "",
        "Delta A (trained vs Week 11 baseline on Tenacious-Bench sealed preference slice)",
        d1,
        "",
        "Delta B (trained vs prompt-only control, same backbone)",
        d2,
        "",
        "Cost / latency (proxy from ablation harness)",
        cost,
        "",
        "Recommendation",
        recommendation,
    ]

    lines_p2 = [
        "Skeptic's appendix (page 2)",
        "",
        "(1) Failure modes Tenacious-Bench v0.1 still under-captures (for v0.2)",
        "- Multi-turn CRM trajectories and long-horizon tool chains (Path C territory).",
        "- Non-English locales and regulated vertical copy not validated in v0.1.",
        "- Human stylistic nuance beyond the mechanical rubric ceiling.",
        "- Adversarial misuse of the bench (overfitting surface patterns without policy understanding).",
        "",
        "(2) Public-signal lossiness",
        "Tasks ground on public and redacted firmographics; real pipelines carry private nuance. ",
        "Scores are necessary but not sufficient for go-live without human spot-checks on novel segments.",
        "",
        "(3) Honest unresolved training issue",
        "GPU memory limits during eval on small T4 runs required skipping full validation curves in ",
        "some sessions (--skip-eval workaround); production monitoring must include periodic eval passes ",
        "on a stable GPU budget.",
        "",
        "(4) Kill-switch trigger (proposed)",
        "Rollback the critic adapter if weekly canary preference accuracy falls below baseline for two ",
        "consecutive weeks, or if task-level rubric regressions exceed agreed tolerance on a fixed audit set.",
        "",
        "Evidence: reports/ablation_results.json, reports/evidence_graph.json, reports/model_card.md, ",
        "GitHub: https://github.com/Hiwot-Beyene/tenacious-bench",
    ]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Tenacious-Bench Week 11 - Decision memo", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    for para in lines_p1:
        pdf.multi_cell(0, 5, para)
        pdf.ln(1)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Appendix - Risks and limits", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    for para in lines_p2:
        pdf.multi_cell(0, 5, para)
        pdf.ln(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(args.out))
    print(json.dumps({"wrote": str(args.out.resolve())}, indent=2))


if __name__ == "__main__":
    main()
