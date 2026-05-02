"""Deterministic rejected-email mutators for Path B preference data.

Each mutator returns (rejected_email, mutator_id, target_dimension_for_verify).
Verification uses evaluation.scoring_evaluator.score_task.

Rejected drafts are finalized with finalize_rejected_below_threshold so overall
score falls below pass_threshold (preference pairs must not have a "winner"
that still passes the global gate).
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from evaluation.scoring_evaluator import score_task

MutatorFn = Callable[[Dict[str, Any], str], Optional[Tuple[str, str, str]]]

# Appended only when base rejected still passes overall threshold; stacks policy violations.
PREFERENCE_ESCALATION_TAIL = (
    "\n\nworld-class synergy top talent.\n"
    "We have 12 engineers on the bench ready to deploy immediately."
)


def verify_rejected(task: Dict[str, Any], rejected: str, *, target_dimension: str) -> bool:
    """True if rejected fails the target rubric dimension (score 1)."""
    res = score_task(task, rejected)
    if res.get("error"):
        return False
    for d in res.get("dimensions") or []:
        if d["name"] == target_dimension and float(d["score"]) <= 1.0:
            return True
    return False


def finalize_rejected_below_threshold(
    task: Dict[str, Any],
    rejected_base: str,
    *,
    target_dimension: str,
) -> Optional[str]:
    """
    If rejected_base still passes task pass_threshold, append PREFERENCE_ESCALATION_TAIL.
    Return None if we cannot produce a strict negative (pass=False) with target_dim still 1.
    """
    r0 = score_task(task, rejected_base)
    if r0.get("error"):
        return None
    out = rejected_base
    if r0.get("pass"):
        out = rejected_base + PREFERENCE_ESCALATION_TAIL
    r1 = score_task(task, out)
    if r1.get("error") or r1.get("pass"):
        return None
    target_ok = any(
        d["name"] == target_dimension and float(d["score"]) <= 1.0 for d in r1.get("dimensions") or []
    )
    if not target_ok:
        return None
    return out


def _split_email(email: str) -> Tuple[str, str]:
    from evaluation.scoring_evaluator import _split_subject_body

    return _split_subject_body(email)


def _join_email(subject: str, body: str) -> str:
    if subject:
        return f"Subject: {subject}\n\n{body}"
    return body


def mut_weak_hard_assert(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    subj, body = _split_email(chosen)
    injection = (
        "\n\nYou are clearly scaling fast based on thin public signals; we should lock staffing now."
    )
    out = _join_email(subj, (body or "") + injection)
    if verify_rejected(task, out, target_dimension="confidence_calibration"):
        return (out, "weak_hard_assert", "confidence_calibration")
    return None


def mut_weak_strip_soft_markers(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    out = chosen
    for m in ("If useful", "if useful", "If relevant", "if relevant", "Are you", "are you", "Is this", "is this"):
        out = out.replace(m, "")
    out = out + "\n\nAggressive hiring is obvious from the outside; no need to confirm."
    if verify_rejected(task, out, target_dimension="confidence_calibration"):
        return (out, "weak_strip_soft_and_assert", "confidence_calibration")
    return None


def mut_bench_risky_template(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    subj, body = _split_email(chosen)
    inj = "\n\nWe can deliver 12 engineers ready to deploy immediately next week."
    out = _join_email(subj, (body or "") + inj)
    if verify_rejected(task, out, target_dimension="bench_safety"):
        return (out, "bench_risky_phrase", "bench_safety")
    return None


def mut_bench_inflate_stack(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    gt = task.get("ground_truth") or {}
    ce = gt.get("capacity_enforcement")
    if not isinstance(ce, dict):
        return None
    subj, body = _split_email(chosen)
    b = body or ""
    new_body, n = re.subn(
        r"(\d+)\s+([Gg]o)\b",
        lambda m: f"{int(m.group(1)) + 50} {m.group(2)}",
        b,
        count=1,
    )
    if n == 0:
        new_body = b + "\n\nOur internal snapshot lists 99 go engineers available."
    out = _join_email(subj, new_body)
    if verify_rejected(task, out, target_dimension="bench_safety"):
        return (out, "bench_inflate_stack", "bench_safety")
    return None


def mut_tone_banned(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    subj, body = _split_email(chosen)
    inj = "\n\nWe are a world-class engineering partner with top talent."
    out = _join_email(subj, (body or "") + inj)
    if verify_rejected(task, out, target_dimension="tone_safety"):
        return (out, "tone_banned_world_class", "tone_safety")
    return None


def mut_tone_bench_word(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    subj, body = _split_email(chosen)
    inj = "\n\nWe have 12 engineers on the bench ready for you this week."
    out = _join_email(subj, (body or "") + inj)
    if verify_rejected(task, out, target_dimension="tone_safety"):
        return (out, "tone_prospect_facing_bench", "tone_safety")
    return None


def mut_gap_condescending(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    subj, body = _split_email(chosen)
    inj = "\n\nYou are clearly behind peer companies on engineering hiring velocity."
    out = _join_email(subj, (body or "") + inj)
    if verify_rejected(task, out, target_dimension="tone_safety"):
        return (out, "gap_condescending_peer", "tone_safety")
    return None


def mut_grounding_strip_signals(task: Dict[str, Any], chosen: str) -> Optional[Tuple[str, str, str]]:
    """Replace email with a generic draft that omits required signals and anchors (grounding miss)."""
    out = _join_email(
        "General follow-up",
        "Hello,\n\nFollowing up on general industry trends.\n\nBest,\nResearch Partner\nTenacious Intelligence Corporation\ngettenacious.com",
    )
    if verify_rejected(task, out, target_dimension="grounding"):
        return (out, "grounding_strip_required_signals", "grounding")
    return None


# (mutator_id, function) — order preserved per dimension
MUTATORS_BY_DIMENSION: Dict[str, List[Tuple[str, MutatorFn]]] = {
    "weak_signal_calibration": [
        ("weak_hard_assert", mut_weak_hard_assert),
        ("weak_strip_soft_and_assert", mut_weak_strip_soft_markers),
        ("grounding_strip_required_signals", mut_grounding_strip_signals),
    ],
    "bench_commitment_safety": [
        ("bench_risky_phrase", mut_bench_risky_template),
        ("bench_inflate_stack", mut_bench_inflate_stack),
        ("tone_prospect_facing_bench", mut_tone_bench_word),
    ],
    "tone_marker_safety": [
        ("tone_banned_world_class", mut_tone_banned),
        ("tone_prospect_facing_bench", mut_tone_bench_word),
        ("bench_risky_phrase", mut_bench_risky_template),
    ],
    "multi_system_coordination": [
        ("tone_prospect_facing_bench", mut_tone_bench_word),
        ("tone_banned_world_class", mut_tone_banned),
        ("bench_risky_phrase", mut_bench_risky_template),
    ],
    "non_condescending_gap_framing": [
        ("gap_condescending_peer", mut_gap_condescending),
        ("tone_banned_world_class", mut_tone_banned),
        ("grounding_strip_required_signals", mut_grounding_strip_signals),
    ],
}


def list_all_mutator_ids() -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for pairs in MUTATORS_BY_DIMENSION.values():
        for mid, _ in pairs:
            if mid not in seen:
                seen.add(mid)
                out.append(mid)
    return sorted(out)


def iter_mutators_for_dimension(
    failure_dimension: str,
    *,
    allowed_ids: Optional[set[str]] = None,
) -> List[Tuple[str, MutatorFn]]:
    pairs = list(MUTATORS_BY_DIMENSION.get(failure_dimension, [("tone_banned_world_class", mut_tone_banned)]))
    if allowed_ids is not None:
        pairs = [(mid, fn) for mid, fn in pairs if mid in allowed_ids]
    return pairs
