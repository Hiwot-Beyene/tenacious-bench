#!/usr/bin/env python3
"""Fail if scenario_catalog does not reference every probe in audit_probe_registry."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bench_corpus.audit_probe_registry import EXPECTED_AUDIT_PROBES  # noqa: E402
from bench_corpus.scenario_catalog import SCENARIOS  # noqa: E402


def collect_catalog_probes() -> set[str]:
    found: set[str] = set()
    for dim, variants in SCENARIOS.items():
        for scen in variants:
            for p in scen.get("audit_probes") or []:
                found.add(str(p))
    return found


def main() -> None:
    catalog = collect_catalog_probes()
    missing = sorted(EXPECTED_AUDIT_PROBES - catalog)
    unexpected = sorted(catalog - EXPECTED_AUDIT_PROBES)
    errs: list[str] = []
    if missing:
        errs.append(f"audit_memo probes missing from scenario_catalog: {missing}")
    if unexpected:
        errs.append(
            "scenario_catalog references probe IDs not in audit_probe_registry.py — "
            f"add to EXPECTED_AUDIT_PROBES if intentional: {unexpected}"
        )
    if errs:
        print("AUDIT PROBE COVERAGE FAIL:\n" + "\n".join(errs))
        raise SystemExit(1)
    print(
        "audit probe coverage OK:",
        len(EXPECTED_AUDIT_PROBES),
        "probes all present in catalog;",
        len(catalog),
        "unique IDs in catalog",
    )


if __name__ == "__main__":
    main()
