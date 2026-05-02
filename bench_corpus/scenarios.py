"""Assemble task dicts from company rows + scenario catalog (see scenario_catalog.py).

**Four authoring modes** (`source_mode` on each task):
- `trace_derived` — Week 10 trace id + lead id bound into provenance.
- `programmatic` — scenario template × **combinatorial slots**: company seed fields (segment,
  region, `employees_bucket`, domain, teaser) × `anchor_packs.build_anchor_ctx` (funding line,
  velocity line, layoff line, leadership line, per-stack bench counts from `internal_capacity_snapshot`).
- `multi_llm_synthesis` — same structured payload; `synthesis_route` records dev-tier bulk model id
  for anti-leakage logs (`generation/model_routing.py`).
- `hand_authored_adversarial` — adversarial rows from the same scenario library with explicit
  provenance.

Train split source-mode marginals target **~30 / 30 / 25 / 15** (`bench_corpus.constants.SOURCE_MODE_TRAIN_SHARE_TARGETS`).
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from bench_corpus.anchor_packs import build_anchor_ctx, slim_capacity_snapshot
from bench_corpus.authoring_modes import build_authoring_metadata, select_catalog_row
from bench_corpus.constants import COMMON_RUBRIC
from bench_corpus.scenario_catalog import SCENARIOS
from bench_corpus.textsafe import public_company_label, safe_domain_hint


def _difficulty(i: int) -> str:
    return ["easy", "medium", "hard"][i % 3]


def _provenance(
    source_mode: str,
    seq: int,
    trace: Optional[Tuple[str, str]],
    synthesis_route: str,
) -> str:
    if source_mode == "trace_derived" and trace:
        tid, lead = trace
        return (
            f"Week 10 trace-anchored reconstruction; trace_id={tid} lead_id={lead}; "
            f"redacted; seq={seq}"
        )
    if source_mode == "multi_llm_synthesis":
        return (
            f"Multi-LLM synthesis slot; routed {synthesis_route}; judge-filtered per methodology; seq={seq}"
        )
    if source_mode == "hand_authored_adversarial":
        return f"Hand-authored adversarial edge case; seq={seq}"
    return f"Programmatic template sweep with structured slots; seq={seq}"


def build_task_payload(
    *,
    seq: int,
    failure_dimension: str,
    partition: str,
    source_mode: str,
    company: Dict[str, Any],
    local_idx: int,
    trace: Optional[Tuple[str, str]],
    synthesis_route: str,
    capacity_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    scen = select_catalog_row(failure_dimension, local_idx, source_mode, SCENARIOS)
    gt: Dict[str, Any] = json.loads(json.dumps(scen["gt"]))

    name = str(company.get("name") or "Prospect")
    domain = str(company.get("domain") or "")
    industry = str(company.get("industry_primary") or company.get("segment_hint") or "B2B")
    segment = str(company.get("segment_hint") or "B2B")
    region = str(company.get("region") or "")
    employees = str(company.get("employees_bucket") or "")
    teaser = str(company.get("about_teaser") or "n/a")

    company_label = public_company_label(name, domain, industry)
    domain_hint = safe_domain_hint(domain)

    ctx: Dict[str, str] = {
        "company": company_label,
        "domain_hint": domain_hint,
        "segment": segment,
        "region": region,
        "employees": employees,
        "about_teaser": teaser,
    }
    ctx.update(build_anchor_ctx(seq, capacity_snapshot))

    brief = scen["brief"].format(**ctx)
    bench = scen["bench"].format(**ctx)
    thread = scen["thread"].format(**ctx)
    body = scen["body"].format(**ctx)

    if failure_dimension == "weak_signal_calibration":
        needle = "Hello,\n\n"
        if needle in body:
            ins = (
                needle
                + f"Public signals include {ctx['named_signal_line']}; posting visibility suggests "
                f"{ctx['named_velocity_line']}. I may still lack internal context.\n\n"
            )
            body = body.replace(needle, ins, 1)

    anchor_keys = list(scen.get("grounding_anchor_keys") or [])
    if anchor_keys:
        gt["grounding_anchors"] = [ctx[k] for k in anchor_keys if ctx.get(k) is not None and str(ctx[k]).strip()]
    elif failure_dimension == "weak_signal_calibration":
        gt["grounding_anchors"] = [ctx["named_signal_line"], ctx["named_velocity_line"]]

    sk_enf = scen.get("enforce_snapshot_stack")
    if sk_enf and capacity_snapshot:
        try:
            mx = int(ctx.get(f"{sk_enf}_available", "0"))
            gt["capacity_enforcement"] = {"stack": sk_enf, "max_available": mx}
        except ValueError:
            pass

    prov = _provenance(source_mode, seq, trace, synthesis_route)
    coverage = {
        "edgecase_tags": list(scen.get("edgecase_tags") or []),
        "icp_segment": scen.get("icp_segment"),
        "audit_probes": list(scen.get("audit_probes") or []),
        "scenario_catalog_version": "v0.4_named_grounding_snapshot",
        "source_mode": source_mode,
        "catalog_authoring_kind": scen.get("authoring_kind"),
    }
    if scen.get("conversion_engine_refs"):
        coverage["conversion_engine_refs"] = list(scen["conversion_engine_refs"])

    input_ctx: Dict[str, Any] = {
        "prospect": {
            "company": name,
            "segment_hint": segment,
            "domain": domain,
            "region": region,
            "employees_bucket": employees,
            "seed_source": company.get("source"),
            "external_id": company.get("external_id"),
        },
        "hiring_signal_brief": brief,
        "bench_summary": bench,
        "prior_thread": thread,
        "provenance_note": prov,
        "public_context_teaser": teaser,
        "coverage": coverage,
    }
    if capacity_snapshot:
        input_ctx["internal_capacity_snapshot"] = slim_capacity_snapshot(capacity_snapshot)

    if source_mode == "trace_derived" and trace:
        tid, lead = trace
        input_ctx["trace_anchor"] = {"trace_id": tid, "lead_id": lead}
    else:
        input_ctx["trace_anchor"] = None

    authoring_meta = build_authoring_metadata(
        source_mode=source_mode,
        failure_dimension=failure_dimension,
        seq=seq,
        local_idx=local_idx,
        company=company,
        scen=scen,
        trace=trace,
        synthesis_route=synthesis_route,
        ctx=ctx,
        capacity_snapshot=capacity_snapshot,
    )

    out: Dict[str, Any] = {
        "task_id": f"tb_v01_{seq:06d}",
        "source_mode": source_mode,
        "failure_dimension": failure_dimension,
        "difficulty": _difficulty(seq),
        "partition": partition,
        "input_context": input_ctx,
        "candidate_output": body,
        "ground_truth": gt,
        "rubric": json.loads(json.dumps(COMMON_RUBRIC)),
        "pass_threshold": 75,
        "coverage": coverage,
        "authoring_metadata": authoring_meta,
    }
    # Dev-tier bulk synthesis route (multi-LLM slots only); judge logs use `generation/model_routing.py`.
    out["synthesis_route"] = synthesis_route if source_mode == "multi_llm_synthesis" else None
    return out
