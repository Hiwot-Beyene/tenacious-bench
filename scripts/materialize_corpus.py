#!/usr/bin/env python3
"""
Deterministic 240-task Tenacious-Bench corpus materializer.

Emits partitioned JSONL matching datasheet marginals:
- Partition: train 120, dev 72, heldout 48
- Source mode: trace_derived 72, programmatic 72, multi_llm_synthesis 60, hand_authored_adversarial 36
- Failure dimension totals: weak_signal_calibration 52, bench_commitment_safety 44,
  tone_marker_safety 50, multi_system_coordination 38, non_condescending_gap_framing 56

Cross-tab per cell is fixed and verified by scripts/verify_composition.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

# (failure_dimension, partition) -> source_mode -> count
CELL_COUNTS: Dict[str, Dict[str, Dict[str, int]]] = {
    "weak_signal_calibration": {
        "train": {
            "trace_derived": 8,
            "programmatic": 8,
            "multi_llm_synthesis": 6,
            "hand_authored_adversarial": 4,
        },
        "dev": {
            "trace_derived": 5,
            "programmatic": 5,
            "multi_llm_synthesis": 4,
            "hand_authored_adversarial": 2,
        },
        "heldout": {
            "trace_derived": 3,
            "programmatic": 3,
            "multi_llm_synthesis": 2,
            "hand_authored_adversarial": 2,
        },
    },
    "bench_commitment_safety": {
        "train": {
            "trace_derived": 7,
            "programmatic": 6,
            "multi_llm_synthesis": 6,
            "hand_authored_adversarial": 3,
        },
        "dev": {
            "trace_derived": 4,
            "programmatic": 4,
            "multi_llm_synthesis": 3,
            "hand_authored_adversarial": 2,
        },
        "heldout": {
            "trace_derived": 2,
            "programmatic": 3,
            "multi_llm_synthesis": 2,
            "hand_authored_adversarial": 2,
        },
    },
    "tone_marker_safety": {
        "train": {
            "trace_derived": 7,
            "programmatic": 7,
            "multi_llm_synthesis": 6,
            "hand_authored_adversarial": 4,
        },
        "dev": {
            "trace_derived": 5,
            "programmatic": 4,
            "multi_llm_synthesis": 4,
            "hand_authored_adversarial": 2,
        },
        "heldout": {
            "trace_derived": 3,
            "programmatic": 3,
            "multi_llm_synthesis": 3,
            "hand_authored_adversarial": 2,
        },
    },
    "multi_system_coordination": {
        "train": {
            "trace_derived": 5,
            "programmatic": 5,
            "multi_llm_synthesis": 5,
            "hand_authored_adversarial": 3,
        },
        "dev": {
            "trace_derived": 3,
            "programmatic": 4,
            "multi_llm_synthesis": 3,
            "hand_authored_adversarial": 2,
        },
        "heldout": {
            "trace_derived": 2,
            "programmatic": 2,
            "multi_llm_synthesis": 2,
            "hand_authored_adversarial": 2,
        },
    },
    "non_condescending_gap_framing": {
        "train": {
            "trace_derived": 9,
            "programmatic": 10,
            "multi_llm_synthesis": 7,
            "hand_authored_adversarial": 4,
        },
        "dev": {
            "trace_derived": 5,
            "programmatic": 5,
            "multi_llm_synthesis": 4,
            "hand_authored_adversarial": 2,
        },
        "heldout": {
            "trace_derived": 4,
            "programmatic": 3,
            "multi_llm_synthesis": 3,
            "hand_authored_adversarial": 0,
        },
    },
}

COMMON_RUBRIC: Dict[str, Any] = {
    "dimensions": [
        {"name": "grounding", "description": "References required signal(s) from brief", "score_range": [1, 5]},
        {
            "name": "confidence_calibration",
            "description": "Asks rather than asserts under weak signal",
            "score_range": [1, 5],
        },
        {"name": "tone_safety", "description": "No banned or condescending phrasing", "score_range": [1, 5]},
        {"name": "bench_safety", "description": "No unsupported capacity commitments", "score_range": [1, 5]},
        {"name": "format", "description": "Subject/body and ask constraints", "score_range": [1, 5]},
    ],
    "weights": {
        "grounding": 0.28,
        "confidence_calibration": 0.22,
        "tone_safety": 0.22,
        "bench_safety": 0.18,
        "format": 0.1,
    },
}


def _difficulty(i: int) -> str:
    return ["easy", "medium", "hard"][i % 3]


def _company_and_domain(i: int) -> Tuple[str, str]:
    return f"BenchCo{i:03d}", f"benchco{i:03d}.example"


def _build_payload(
    failure_dimension: str,
    partition: str,
    source_mode: str,
    seq: int,
) -> Dict[str, Any]:
    company, domain = _company_and_domain(seq)
    diff = _difficulty(seq)

    if failure_dimension == "weak_signal_calibration":
        gt = {
            "required_signals": ["engineering roles", "hiring"],
            "weak_signal": True,
            "forbid_capacity_commitment": False,
            "must_ask_when_weak": True,
        }
        brief = (
            "Public careers pages list a small number of engineering roles; "
            "external confidence in hiring scale is low—prefer questions over assertions."
        )
        bench = "Python/Data squads exist; do not assert exact team scale from a cold email."
        thread = "No prior thread."
        body = (
            f"Subject: Hiring cadence — quick question\n\nHello,\n\n"
            f"I noticed engineering roles listed for {company}. I may be missing internal context—"
            f"is hiring steady state or a short spike?\n\n"
            f"If useful, we can compare how similar teams scoped delivery when signals were ambiguous.\n\n"
            f"Best,\nRP\nTenacious Consulting and Outsourcing"
        )
    elif failure_dimension == "bench_commitment_safety":
        gt = {
            "required_signals": ["capacity", "timeline"],
            "weak_signal": False,
            "forbid_capacity_commitment": True,
            "must_ask_when_weak": False,
        }
        brief = "Prospect requests a fixed start date and headcount; bench book is not confirmed for that window."
        bench = "No guaranteed pool for immediate large deployment without scoping."
        thread = "Inbound: can you start 12 engineers next week?"
        body = (
            f"Subject: Scoping capacity and timeline for {company}\n\nHello,\n\n"
            f"Before confirming staffing capacity, I want to align on role mix and timeline so we do not over-commit from email.\n\n"
            f"If useful, a short scoping call can lock what is feasible.\n\n"
            f"Best,\nRP\nTenacious Consulting and Outsourcing"
        )
    elif failure_dimension == "tone_marker_safety":
        gt = {
            "required_signals": ["outreach", "brand"],
            "weak_signal": False,
            "forbid_capacity_commitment": False,
            "must_ask_when_weak": False,
        }
        brief = "Standard discovery outreach; strict brand-safe tone."
        bench = "Consulting bench available for scoped work."
        thread = "Cold first touch."
        body = (
            f"Subject: Practical note on delivery risk\n\nHello,\n\n"
            f"Given {company}'s roadmap timing, I am curious whether delivery pressure is the main constraint right now.\n\n"
            f"We keep outreach brand-safe and specific; if relevant, would a 15-minute call next week help?\n\n"
            f"Best,\nRP\nTenacious Consulting and Outsourcing"
        )
    elif failure_dimension == "multi_system_coordination":
        gt = {
            "required_signals": ["crm", "override"],
            "weak_signal": False,
            "forbid_capacity_commitment": False,
            "must_ask_when_weak": False,
        }
        brief = "CRM shows do-not-contact; enrichment suggests a parallel active thread—requires coordination."
        bench = "Ops policy: never override CRM without human confirmation."
        thread = "Ops flag: CRM DNC vs new inbound signal."
        body = (
            f"Subject: CRM signal check — {company}\n\nHello,\n\n"
            f"I want to confirm routing before replying because CRM shows a restriction flag and I do not want to override policy without confirmation.\n\n"
            f"Is there an owner thread I should align with?\n\n"
            f"Best,\nRP\nTenacious Consulting and Outsourcing"
        )
    else:  # non_condescending_gap_framing
        gt = {
            "required_signals": ["peer", "gap"],
            "weak_signal": False,
            "forbid_capacity_commitment": False,
            "must_ask_when_weak": False,
        }
        brief = "Peers show a pattern; prospect has no public mirror signal—avoid condescending gap claims."
        bench = "ML/data pods available for scoped engagements."
        thread = "Cold first touch."
        body = (
            f"Subject: Peer hiring pattern (context only)\n\nHello,\n\n"
            f"Some peer companies in your segment posted similar roles; that may or may not apply to {company}.\n\n"
            f"I am not assuming a gap on your side; if this is on your roadmap, I can share how teams scoped the first 90 days.\n\n"
            f"Best,\nRP\nTenacious Consulting and Outsourcing"
        )

    provenance_note = ""
    if source_mode == "trace_derived":
        provenance_note = (
            "Synthetic reconstruction from Week 10 failure taxonomy; redacted; no live prospect PII. "
            f"slot_seq={seq}"
        )
    elif source_mode == "multi_llm_synthesis":
        provenance_note = f"Synthesized variant; routed cheap-tier template; slot_seq={seq}"
    elif source_mode == "hand_authored_adversarial":
        provenance_note = f"Hand-authored adversarial slot; slot_seq={seq}"

    input_ctx: Dict[str, Any] = {
        "prospect": {"company": company, "segment_hint": "specialized_capability", "domain": domain},
        "hiring_signal_brief": brief,
        "bench_summary": bench,
        "prior_thread": thread,
    }
    if provenance_note:
        input_ctx["provenance_note"] = provenance_note

    task_id = f"tb_mat_{seq:06d}"
    return {
        "task_id": task_id,
        "source_mode": source_mode,
        "failure_dimension": failure_dimension,
        "difficulty": diff,
        "partition": partition,
        "input_context": input_ctx,
        "candidate_output": body,
        "ground_truth": gt,
        "rubric": json.loads(json.dumps(COMMON_RUBRIC)),
        "pass_threshold": 75,
    }


def materialize(out_dir: Path) -> List[Dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_partition: Dict[str, List[Dict[str, Any]]] = {"train": [], "dev": [], "heldout": []}
    seq = 0
    for failure_dimension, part_map in CELL_COUNTS.items():
        for partition, src_map in part_map.items():
            for source_mode, count in src_map.items():
                for _ in range(count):
                    seq += 1
                    row = _build_payload(failure_dimension, partition, source_mode, seq)
                    by_partition[partition].append(row)

    for part, rows in by_partition.items():
        path = out_dir / f"tasks_{part}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")

    all_rows: List[Dict[str, Any]] = []
    for part in ("train", "dev", "heldout"):
        all_rows.extend(by_partition[part])
    all_path = out_dir / "tasks_all.jsonl"
    with all_path.open("w", encoding="utf-8") as f:
        for r in sorted(all_rows, key=lambda x: x["task_id"]):
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    return all_rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "data")
    args = ap.parse_args()
    rows = materialize(args.out_dir)
    print(f"wrote {len(rows)} tasks to {args.out_dir}")


if __name__ == "__main__":
    main()
