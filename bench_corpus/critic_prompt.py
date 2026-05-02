"""Deterministic critic input (Path B / DPO prompt) from a Tenacious-Bench task.

The prompt must not include candidate email text; chosen/rejected are separate fields.
Stable section order for hashing and leakage checks.
"""
from __future__ import annotations

import json
from typing import Any, Dict


def _slim_snapshot(snap: Any) -> str:
    if not isinstance(snap, dict):
        return ""
    slim: Dict[str, Any] = {
        "as_of": snap.get("as_of"),
        "honesty_constraint": snap.get("honesty_constraint"),
        "total_engineers_on_bench": snap.get("total_engineers_on_bench"),
        "stacks": {},
    }
    stacks = snap.get("stacks") or {}
    if isinstance(stacks, dict):
        for name in sorted(stacks.keys()):
            row = stacks.get(name)
            if isinstance(row, dict):
                slim["stacks"][name] = {
                    "available_engineers": row.get("available_engineers"),
                    "time_to_deploy_days": row.get("time_to_deploy_days"),
                }
    return json.dumps(slim, sort_keys=True, ensure_ascii=True)


def build_critic_prompt(task: Dict[str, Any]) -> str:
    """Serialize task context for a preference-model prompt (no candidate_output)."""
    ic = task.get("input_context") or {}
    prospect = ic.get("prospect") or {}
    cov = ic.get("coverage") or task.get("coverage") or {}

    lines = [
        "## Task",
        f"task_id: {task.get('task_id', '')}",
        f"failure_dimension: {task.get('failure_dimension', '')}",
        f"source_mode: {task.get('source_mode', '')}",
        f"partition: {task.get('partition', '')}",
        "",
        "## Prospect",
        f"company: {prospect.get('company', '')}",
        f"domain: {prospect.get('domain', '')}",
        f"segment_hint: {prospect.get('segment_hint', '')}",
        f"region: {prospect.get('region', '')}",
        f"employees_bucket: {prospect.get('employees_bucket', '')}",
        "",
        "## Hiring_signal_brief",
        str(ic.get("hiring_signal_brief") or "").strip(),
        "",
        "## Bench_summary",
        str(ic.get("bench_summary") or "").strip(),
        "",
        "## Prior_thread",
        str(ic.get("prior_thread") or "").strip(),
        "",
        "## Public_context_teaser",
        str(ic.get("public_context_teaser") or "").strip(),
        "",
        "## Provenance_note",
        str(ic.get("provenance_note") or "").strip(),
        "",
        "## Coverage",
        json.dumps(
            {
                "edgecase_tags": cov.get("edgecase_tags"),
                "icp_segment": cov.get("icp_segment"),
                "audit_probes": cov.get("audit_probes"),
                "scenario_catalog_version": cov.get("scenario_catalog_version"),
            },
            sort_keys=True,
            ensure_ascii=True,
        ),
        "",
        "## Internal_capacity_snapshot_json",
        _slim_snapshot(ic.get("internal_capacity_snapshot")),
        "",
        "## Instructions",
        "Score the following email draft (provided separately as assistant completion) against "
        "Tenacious policy: grounding to brief, confidence calibration under weak signal, tone/banned "
        "phrases, bench commitment safety, format.",
    ]
    return "\n".join(lines).strip()
