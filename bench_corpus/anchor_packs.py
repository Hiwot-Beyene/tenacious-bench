"""Deterministic named-signal lines + capacity snapshot fields for Style Guide v2-style grounding."""
from __future__ import annotations

from typing import Any, Dict, Optional


def _stack_avail(snapshot: Optional[Dict[str, Any]], key: str) -> int:
    if not snapshot:
        return 0
    stacks = snapshot.get("stacks") or {}
    row = stacks.get(key) or {}
    return int(row.get("available_engineers") or 0)


def build_anchor_ctx(seq: int, capacity_snapshot: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    Per-task context keys for .format() in scenario templates.
    Rotates verifiable phrases so grounding_anchors differ across tasks.
    """
    funding = [
        "a $14M Series A referenced publicly for February 2025",
        "a $22M Series B referenced publicly for January 2025",
        "a $9M seed extension referenced publicly for October 2025",
        "a $18M Series A referenced publicly for March 2025",
    ]
    velocity = [
        "seven open engineering roles indexed in the last 60 days",
        "five public engineering postings with mixed board agreement",
        "a thin set of two to three engineering roles on careers pages",
        "roughly a dozen public engineering postings after de-duplication",
    ]
    layoff = [
        "a ~12% workforce contraction discussed publicly in March",
        "an ~8% restructuring note in public press in April",
        "workforce-change commentary in public trackers in Q1",
    ]
    leadership = [
        "a CTO appointment announcement dated the 14th of last month",
        "a VP Engineering transition referenced on the company site in the last 90 days",
        "a new engineering leader post visible within the standard 90-day reassessment window",
    ]
    i = seq % 4
    j = (seq // 3) % 4
    k = (seq // 5) % 3
    m = (seq // 7) % 3

    ctx: Dict[str, str] = {
        "named_signal_line": funding[i],
        "named_velocity_line": velocity[j],
        "named_layoff_line": layoff[k],
        "named_leadership_line": leadership[m],
    }

    if capacity_snapshot:
        ctx["snapshot_as_of"] = str(capacity_snapshot.get("as_of") or "unknown")
        for sk in ("python", "go", "data", "ml", "infra", "frontend"):
            ctx[f"{sk}_available"] = str(_stack_avail(capacity_snapshot, sk))
        ctx["capacity_honesty_note"] = str(
            (capacity_snapshot.get("honesty_constraint") or "")[:280]
        )
    else:
        ctx["snapshot_as_of"] = "unavailable"
        for sk in ("python", "go", "data", "ml", "infra", "frontend"):
            ctx[f"{sk}_available"] = "0"
        ctx["capacity_honesty_note"] = ""

    return ctx


def slim_capacity_snapshot(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Strip heavy arrays for JSONL; keep counts + deploy days + leadership tallies."""
    out: Dict[str, Any] = {
        "as_of": raw.get("as_of"),
        "notes": raw.get("notes"),
        "honesty_constraint": raw.get("honesty_constraint"),
        "total_engineers_on_bench": raw.get("total_engineers_on_bench"),
        "stacks": {},
    }
    stacks = raw.get("stacks") or {}
    for name, row in stacks.items():
        if not isinstance(row, dict):
            continue
        out["stacks"][name] = {
            "available_engineers": row.get("available_engineers"),
            "time_to_deploy_days": row.get("time_to_deploy_days"),
            "note": row.get("note"),
        }
    if isinstance(raw.get("leadership"), dict):
        out["leadership"] = raw["leadership"]
    return out


def load_bench_summary_json(path: Any) -> Optional[Dict[str, Any]]:
    try:
        import json
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
