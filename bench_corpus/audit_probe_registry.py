"""Canonical ADV probe IDs from docs/audit_memo.md (Week 10 failure taxonomy).

Used by scripts/verify_audit_probe_coverage.py to ensure the scenario catalog
tags every audit-class failure the memo promises to cover.
"""
from __future__ import annotations

from typing import FrozenSet

# Paragraph-level probe families cited in audit_memo.md
EXPECTED_AUDIT_PROBES: FrozenSet[str] = frozenset(
    {
        "ADV-SIG-01",
        "ADV-SIG-02",
        "ADV-SIG-03",
        "ADV-SIG-04",
        "ADV-BNC-01",
        "ADV-BNC-02",
        "ADV-BNC-03",
        "ADV-BNC-04",
        "ADV-TON-01",
        "ADV-TON-02",
        "ADV-TON-03",
        "ADV-TON-04",
        "ADV-TON-05",
        "ADV-DUL-01",
        "ADV-DUL-02",
        "ADV-MLT-01",
        "ADV-MLT-02",
        "ADV-GAP-01",
        "ADV-GAP-02",
        "ADV-GAP-03",
        "ADV-GAP-04",
    }
)
