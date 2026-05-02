"""Four-mode dataset authoring — Week 11 rubric entry point.

This module ties grading criteria to concrete code paths:

1. ``trace_derived`` — Week 10 trace anchors from ``bench_corpus.seeds.load_trace_anchors``;
   structured ``authoring_metadata["trace_anchor"]`` plus ``input_context.trace_anchor``.
2. ``programmatic`` — Scenario template × **combinatorial** company slots (segment, region,
   ``employees_bucket`` / headcount, domain, teaser) × ``anchor_packs.build_anchor_ctx`` (rotated
   funding/velocity/layoff/leadership lines + per-stack bench counts from ``internal_capacity_snapshot``).
3. ``multi_llm_synthesis`` — Same combinatorial shell; bulk author model id from
   ``generation.model_routing.pick_bulk_generator`` (``synthesis_route`` on the task when this mode is active).
4. ``hand_authored_adversarial`` — Curated catalog rows with ``authoring_kind == "hand_adversarial"``
   (assigned by ``tag_scenario_rows``): dual-source / override stress, multi-probe, and high-risk audit IDs.

**Share targets (train split, approximate):** 30% / 30% / 25% / 15% for the four modes — see
``bench_corpus.constants.SOURCE_MODE_TRAIN_SHARE_TARGETS`` and integer ``CELL_COUNTS``; realized
margins are checked in ``scripts/verify_composition.py``.

Orchestration: ``scripts/build_corpus.py`` → ``scenarios.build_task_payload``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Probes / patterns that mark human-curated adversarial *templates* (vs. baseline programmatic sweep rows).
_STRESS_PROBES_HAND = frozenset(
    {
        "ADV-BNC-04",
        "ADV-TON-03",
        "ADV-TON-04",
        "ADV-TON-05",
        "ADV-GAP-04",
        "ADV-GAP-03",
    }
)

# Synthetic sweep bucket for methodology visibility (company seeds rarely carry a numeric maturity score).
_AI_MATURITY_SWEEP_BUCKETS = (
    "public_unknown",
    "0_1_exploratory",
    "2_3_active",
    "4_plus_caution",
    "gated_segment4_hint",
)


def row_is_hand_adversarial(failure_dimension: str, row: Dict[str, Any]) -> bool:
    req = set(row.get("gt", {}).get("required_signals") or [])
    probes = [str(p) for p in (row.get("audit_probes") or [])]
    if any(p.startswith("ADV-DUL") for p in probes):
        return True
    if failure_dimension == "multi_system_coordination":
        return "override" in req and any(p.startswith("ADV-MLT") for p in probes)
    if set(probes) & _STRESS_PROBES_HAND:
        return True
    if len(probes) >= 2:
        return True
    return False


def tag_scenario_rows(scenarios: Dict[str, List[Dict[str, Any]]]) -> None:
    """Mutate catalog rows in place: ``authoring_kind`` is ``hand_adversarial`` or ``programmatic_template``."""
    for fd, rows in scenarios.items():
        for r in rows:
            r["authoring_kind"] = (
                "hand_adversarial" if row_is_hand_adversarial(fd, r) else "programmatic_template"
            )


def select_catalog_row(
    failure_dimension: str,
    local_idx: int,
    source_mode: str,
    scenarios: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    variants = scenarios[failure_dimension]
    if source_mode == "hand_authored_adversarial":
        pool = [v for v in variants if v.get("authoring_kind") == "hand_adversarial"]
        if not pool:
            pool = variants
    else:
        pool = [v for v in variants if v.get("authoring_kind") != "hand_adversarial"]
        if not pool:
            pool = variants
    return pool[local_idx % len(pool)]


def build_authoring_metadata(
    *,
    source_mode: str,
    failure_dimension: str,
    seq: int,
    local_idx: int,
    company: Dict[str, Any],
    scen: Dict[str, Any],
    trace: Optional[Tuple[str, str]],
    synthesis_route: str,
    ctx: Dict[str, str],
    capacity_snapshot: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    from bench_corpus.anchor_packs import anchor_rotation_indices, slim_capacity_snapshot
    from bench_corpus.constants import SOURCE_MODE_TRAIN_SHARE_TARGETS

    slim = slim_capacity_snapshot(capacity_snapshot) if capacity_snapshot else None
    stack_available: Dict[str, int] = {}
    if slim and isinstance(slim.get("stacks"), dict):
        for name, row in slim["stacks"].items():
            if isinstance(row, dict):
                try:
                    stack_available[str(name)] = int(row.get("available_engineers") or 0)
                except (TypeError, ValueError):
                    stack_available[str(name)] = 0

    meta: Dict[str, Any] = {
        "task_source_mode": source_mode,
        "failure_dimension": failure_dimension,
        "catalog_authoring_kind": scen.get("authoring_kind"),
        "train_share_targets_reference": "bench_corpus.constants.SOURCE_MODE_TRAIN_SHARE_TARGETS",
        "train_share_target_fractions": dict(SOURCE_MODE_TRAIN_SHARE_TARGETS),
        "combinatorial_slots": {
            "company_segment": str(company.get("segment_hint") or ""),
            "company_region": str(company.get("region") or ""),
            "company_employees_bucket": str(company.get("employees_bucket") or ""),
            "company_domain": str(company.get("domain") or ""),
            "public_context_teaser_excerpt": (str(company.get("about_teaser") or "")[:120] or None),
            "icp_segment_template": scen.get("icp_segment"),
            "ai_maturity_sweep_bucket": _AI_MATURITY_SWEEP_BUCKETS[seq % len(_AI_MATURITY_SWEEP_BUCKETS)],
            "anchor_rotation": anchor_rotation_indices(seq),
            "bench_snapshot_as_of": (slim or {}).get("as_of"),
            "bench_stack_available_engineers": stack_available or None,
            "named_signal_excerpt": (ctx.get("named_signal_line") or "")[:80] or None,
        },
        "corpus_builder_local_idx": local_idx,
    }
    if source_mode == "trace_derived" and trace:
        tid, lead = trace
        meta["trace_anchor"] = {"trace_id": tid, "lead_id": lead}
    else:
        meta["trace_anchor"] = None

    if source_mode == "multi_llm_synthesis":
        meta["synthesis_route_model_id"] = synthesis_route
    else:
        meta["synthesis_route_model_id"] = None

    return meta
