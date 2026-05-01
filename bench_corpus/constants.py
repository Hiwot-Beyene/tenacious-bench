"""Fixed composition targets for Tenacious-Bench v0.1 (datasheet marginals)."""
from __future__ import annotations

from typing import Any, Dict

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
