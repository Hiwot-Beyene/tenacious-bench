"""Pointwise task-quality judge (1–5) aligned with `prompts/judge_pointwise.md`.

v0.1 default: **mechanical** scoring so CI and air-gapped builds reproduce logs without API keys.
When `OPENROUTER_API_KEY` is set, use `generation/openrouter_judge.py` (optional HTTP) for the
same three dimensions; thresholds stay in `generation/judge_filter.py`.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def mechanical_pointwise_scores(task: Dict[str, Any]) -> Tuple[Dict[str, int], List[str]]:
    """
    Returns (scores dict, diagnostic notes — not fail_reasons; pipeline adds those vs thresholds).
    Scale 1–5 per prompts/judge_pointwise.md.
    """
    notes: List[str] = []
    ic = task.get("input_context") or {}
    brief = str(ic.get("hiring_signal_brief") or "")
    bench = str(ic.get("bench_summary") or "")
    thread = str(ic.get("prior_thread") or "")
    teaser = str(ic.get("public_context_teaser") or "")
    prospect = ic.get("prospect") or {}
    company = str(prospect.get("company") or "")
    domain = str(prospect.get("domain") or "")

    # --- input_coherence (allow one short thread line if brief+bench are strong)
    field_lens = [len(brief), len(bench), len(thread), len(teaser)]
    weak = sum(1 for L in field_lens if L < 28)
    core_ok = len(brief) >= 45 and len(bench) >= 40
    if weak == 0 and company and domain:
        input_coherence = 5
    elif weak <= 1 and company and core_ok:
        input_coherence = 5
        notes.append("one_context_field_short")
    elif weak <= 1 and company:
        input_coherence = 4
        notes.append("one_context_field_short")
    elif weak <= 2 and core_ok:
        input_coherence = 4
        notes.append("thin_context")
    elif weak <= 2:
        input_coherence = 3
        notes.append("thin_context")
    else:
        input_coherence = 2
        notes.append("sparse_context")

    # --- ground_truth_verifiability
    gt = task.get("ground_truth") or {}
    anchors = gt.get("grounding_anchors")
    ce = gt.get("capacity_enforcement")
    has_anchors = isinstance(anchors, list) and len(anchors) > 0
    has_ce = isinstance(ce, dict) and bool(ce.get("stack") or ce.get("max_available") is not None)
    cov = ic.get("coverage") or task.get("coverage") or {}
    probes = cov.get("audit_probes") or []
    has_probes = isinstance(probes, list) and len(probes) > 0
    gt_has_rubric_hooks = isinstance(gt, dict) and bool(
        gt.get("required_signals")
        or gt.get("weak_signal") is not None
        or gt.get("forbid_capacity_commitment") is not None
    )

    if has_probes and has_anchors:
        ground_truth_verifiability = 5
    elif has_probes and (has_ce or gt_has_rubric_hooks):
        ground_truth_verifiability = 5
        if not has_anchors and not has_ce:
            notes.append("gt_verifiable_without_named_anchors")
    elif has_anchors or has_ce:
        ground_truth_verifiability = 4
        if not has_probes:
            notes.append("no_audit_probes")
    elif has_probes:
        ground_truth_verifiability = 3
        notes.append("weak_gt_structure")
    else:
        ground_truth_verifiability = 2
        notes.append("gt_sparse")

    # --- rubric_application_clarity
    rub = task.get("rubric") or {}
    dims = rub.get("dimensions") or []
    weights = rub.get("weights") or {}
    n_dim = len(dims) if isinstance(dims, list) else 0
    wsum = sum(float(v) for v in weights.values()) if isinstance(weights, dict) else 0.0
    if n_dim >= 5 and 0.99 <= wsum <= 1.01:
        rubric_application_clarity = 5
    elif n_dim >= 5:
        rubric_application_clarity = 4
        notes.append("rubric_weights_not_normalized")
    elif n_dim >= 3:
        rubric_application_clarity = 3
        notes.append("partial_rubric")
    else:
        rubric_application_clarity = 2
        notes.append("rubric_incomplete")

    scores = {
        "input_coherence": input_coherence,
        "ground_truth_verifiability": ground_truth_verifiability,
        "rubric_application_clarity": rubric_application_clarity,
    }
    return scores, notes
