#!/usr/bin/env python3
"""Structural checks on scenario_catalog rows (metadata for coverage / grading traceability)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.scenario_catalog import SCENARIOS  # noqa: E402

REQUIRED_TOP_KEYS = ("gt", "brief", "bench", "thread", "body")
REQUIRED_GT_KEYS = ("required_signals", "weak_signal", "forbid_capacity_commitment", "must_ask_when_weak")


def _err(msgs: List[str], msg: str) -> None:
    msgs.append(msg)


def main() -> None:
    msgs: List[str] = []
    for dim, variants in SCENARIOS.items():
        for i, scen in enumerate(variants):
            label = f"{dim}[{i}]"
            if not isinstance(scen, dict):
                _err(msgs, f"{label}: scenario must be dict")
                continue
            for k in REQUIRED_TOP_KEYS:
                if k not in scen or not str(scen.get(k) or "").strip():
                    _err(msgs, f"{label}: missing or empty {k!r}")
            gt = scen.get("gt")
            if not isinstance(gt, dict):
                _err(msgs, f"{label}: gt must be dict")
            else:
                for gk in REQUIRED_GT_KEYS:
                    if gk not in gt:
                        _err(msgs, f"{label}: ground_truth missing {gk!r}")
                rs = gt.get("required_signals")
                if not isinstance(rs, list) or not rs:
                    _err(msgs, f"{label}: required_signals must be non-empty list")
            tags = scen.get("edgecase_tags")
            if not isinstance(tags, list) or not tags:
                _err(msgs, f"{label}: edgecase_tags must be non-empty list")
            probes = scen.get("audit_probes")
            if not isinstance(probes, list) or not probes:
                _err(msgs, f"{label}: audit_probes must be non-empty list")
            kind = scen.get("authoring_kind")
            if kind not in ("hand_adversarial", "programmatic_template"):
                _err(msgs, f"{label}: authoring_kind must be set (run scenario_catalog load / tag_scenario_rows)")
            for k in ("brief", "bench", "thread", "body"):
                blob = str(scen.get(k) or "")
                if "{" in blob and k != "body":
                    for ph in ("company", "domain_hint", "segment", "region", "employees", "about_teaser"):
                        if "{" + ph + "}" in blob:
                            break
                    else:
                        if any(c + "}" in blob for c in "{snapshot_as_of go_available python_available".split()):
                            pass
                        elif "{" in blob:
                            _err(msgs, f"{label}: {k} has {{}} placeholders — verify ctx keys in scenarios.py")

    if msgs:
        print("SCENARIO CATALOG INTEGRITY FAIL:\n" + "\n".join(msgs[:80]))
        if len(msgs) > 80:
            print(f"... and {len(msgs) - 80} more")
        raise SystemExit(1)

    n = sum(len(v) for v in SCENARIOS.values())
    print("scenario catalog integrity OK:", n, "rows across", len(SCENARIOS), "dimensions")


if __name__ == "__main__":
    main()
