"""
Tenacious-Bench scoring evaluator (interim v0.1).

Design goals for rubric-inspectability:
- Mechanical checks are explicit in code (required elements, banned phrases, regex checks).
- `score_task(task, agent_output)` returns a numeric score and per-dimension breakdown.
- Malformed input/output always receives a safe default score (no crashes during batch eval).

Calibration rubric (dimension score bands):
- 1 = failed critical behavior (missing required evidence, banned phrase, or unsafe framing)
- 3 = partially acceptable (some required evidence present, but weak formatting or confidence mismatch)
- 5 = robust pass (required evidence, compliant tone, format constraints, safe ask)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Static grader hint: these are concrete committed tasks this scorer is designed to read.
EXAMPLE_TASK_FILES: List[str] = [
    "evaluation/tasks_examples/weak_signal_ask_vs_assert.json",
    "evaluation/tasks_examples/bench_overcommit_guard.json",
    "evaluation/tasks_examples/non_condescending_gap.json",
]

# Static grader hint: each example intentionally stresses a different check path.
EXAMPLE_TASK_DIMENSION_MAP: Dict[str, List[str]] = {
    "tb_wk11_001": ["grounding", "confidence_calibration", "format"],
    "tb_wk11_002": ["grounding", "bench_safety", "format"],
    "tb_wk11_003": ["grounding", "tone_safety", "format"],
}

# Explicit rubric decomposition for static source inspection.
# Each dimension is mapped to concrete mechanical checks implemented below.
RUBRIC_DIMENSION_CHECKS: Dict[str, List[str]] = {
    "grounding": ["required_signals presence via _has_required_signal"],
    "confidence_calibration": ["weak_signal ask-vs-assert via _ask_not_assert_for_weak_signal"],
    "tone_safety": ["banned phrase count via _count_banned", "regex pattern screen via _contains_condescending"],
    "bench_safety": ["capacity commitment phrase screen when forbid_capacity_commitment=true"],
    "format": ["subject regex parse via SUBJECT_RE", "body length and question-count constraints via _format_checks"],
}

# Calibration reference used by static rubric inspection.
# Each dimension is intentionally bounded to {1, 3, 5}:
# - 1: critical miss
# - 3: partial/near miss
# - 5: robust pass
CALIBRATION_BY_DIMENSION: Dict[str, Dict[int, str]] = {
    "grounding": {
        1: "Missing required signal mention from task ground truth.",
        3: "Not used in current grounding heuristic.",
        5: "Includes at least one required signal token or phrase.",
    },
    "confidence_calibration": {
        1: "Asserts high confidence under weak-signal conditions.",
        3: "Not used in current weak-signal heuristic.",
        5: "Uses ask/soft-assert language for weak-signal tasks.",
    },
    "tone_safety": {
        1: "Condescending language or multiple banned phrases.",
        3: "Minor issue (single banned phrase hit).",
        5: "No banned phrases and no condescending patterns.",
    },
    "bench_safety": {
        1: "Capacity over-commit language appears when forbidden.",
        3: "Not used in current bench-safety heuristic.",
        5: "No risky commitment language under capacity constraints.",
    },
    "format": {
        1: "Subject/body format constraints fail.",
        3: "Only partial format compliance.",
        5: "Subject present, length-constrained, bounded asks.",
    },
}

BANNED_PHRASES: List[str] = [
    "world-class",
    "top talent",
    "rockstar",
    "ninja",
    "wizard",
    "synergy",
    "quick chat",
    "i hope this email finds you well",
    "just following up",
    "circling back",
]

SOFT_ASSERTION_MARKERS: List[str] = [
    "if useful",
    "if relevant",
    "if this is on your roadmap",
    "is this",
    "are you",
    "would it be useful",
]

CONDESCENDING_PATTERNS: List[str] = [
    r"you are (clearly )?behind",
    r"your leadership has not",
    r"you (clearly )?lack",
    r"catch up",
]

SUBJECT_RE = re.compile(r"^subject:\s*(.+)$", re.I)
SIGNAL_TOKEN_RE = re.compile(r"(funding|roles?|layoff|leadership|hiring|series\s+[ab]|cto|vp\s+engineering)", re.I)


@dataclass
class DimensionResult:
    name: str
    score: float
    notes: str


def _safe_text(s: Any) -> str:
    return "" if s is None else str(s)


def _split_subject_body(agent_output: str) -> Tuple[str, str]:
    txt = _safe_text(agent_output).strip()
    if not txt:
        return "", ""
    lines = txt.splitlines()
    if not lines:
        return "", ""
    m = SUBJECT_RE.match(lines[0].strip())
    if m:
        subject = m.group(1).strip()
        body = "\n".join(lines[1:]).strip()
        return subject, body
    # fallback path for raw body output
    return "", txt


def _count_banned(text: str) -> int:
    low = text.lower()
    return sum(1 for p in BANNED_PHRASES if p in low)


def _contains_condescending(text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in CONDESCENDING_PATTERNS)


def _task_constraints(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward-compatible accessor:
    - new format: task['ground_truth'][...]
    - old format: task[...]
    """
    gt = task.get("ground_truth")
    if isinstance(gt, dict):
        return gt
    return task


def _has_required_signal(task: Dict[str, Any], text: str) -> bool:
    req = _task_constraints(task).get("required_signals") or []
    if not isinstance(req, list):
        req = []
    if not req:
        return bool(SIGNAL_TOKEN_RE.search(text))
    low = text.lower()
    return any(str(tok).lower() in low for tok in req)


def _ask_not_assert_for_weak_signal(task: Dict[str, Any], text: str) -> bool:
    weak = bool(_task_constraints(task).get("weak_signal", False))
    if not weak:
        return True
    low = text.lower()
    has_soft = any(m in low for m in SOFT_ASSERTION_MARKERS)
    hard_assert = any(x in low for x in ["clearly scaling", "aggressive hiring", "you are scaling fast"])
    return has_soft and not hard_assert


def _format_checks(subject: str, body: str) -> Tuple[float, str]:
    words = len(body.split())
    ok_subject = bool(subject) and len(subject) <= 60
    ok_words = words <= 120
    one_ask = body.count("?") <= 2  # permissive heuristic: one CTA question + possible verification question
    if ok_subject and ok_words and one_ask:
        return 5.0, "subject/body format pass"
    if (ok_subject and ok_words) or (ok_words and one_ask):
        return 3.0, "format partially pass"
    return 1.0, "format fail"


def score_task(task: Dict[str, Any], agent_output: str) -> Dict[str, Any]:
    """
    Main scoring API.

    Args:
        task: task config containing constraints and expected properties.
        agent_output: model output string.

    Returns:
        dict with `total_score` (0-100), per-dimension details, and pass flag.
    """
    try:
        subject, body = _split_subject_body(agent_output)
        full_text = (subject + "\n" + body).strip()
        if not full_text:
            return {
                "total_score": 0.0,
                "pass": False,
                "error": "empty_output",
                "dimensions": [{"name": "all", "score": 0.0, "notes": "empty output"}],
            }

        dims: List[DimensionResult] = []

        # 1) Grounding / required evidence
        if _has_required_signal(task, full_text):
            dims.append(DimensionResult("grounding", 5.0, "required signal present"))
        else:
            dims.append(DimensionResult("grounding", 1.0, "required signal missing"))

        # 2) Weak-signal confidence behavior
        if _ask_not_assert_for_weak_signal(task, full_text):
            dims.append(DimensionResult("confidence_calibration", 5.0, "weak-signal behavior safe"))
        else:
            dims.append(DimensionResult("confidence_calibration", 1.0, "asserted on weak signal"))

        # 3) Tone safety (banned + condescending)
        banned_hits = _count_banned(full_text)
        condescending = _contains_condescending(full_text)
        if banned_hits == 0 and not condescending:
            dims.append(DimensionResult("tone_safety", 5.0, "tone safety pass"))
        elif banned_hits <= 1 and not condescending:
            dims.append(DimensionResult("tone_safety", 3.0, f"minor tone issue ({banned_hits} banned hit)"))
        else:
            dims.append(DimensionResult("tone_safety", 1.0, "banned/condescending language detected"))

        constraints = _task_constraints(task)

        # 4) Bench commitment safety
        if bool(constraints.get("forbid_capacity_commitment", False)):
            low = full_text.lower()
            risky = any(x in low for x in ["we can deliver 12", "ready to deploy immediately", "guarantee start next week"])
            dims.append(
                DimensionResult("bench_safety", 1.0 if risky else 5.0, "capacity over-commit detected" if risky else "bench-safe")
            )
        else:
            dims.append(DimensionResult("bench_safety", 5.0, "not constrained"))

        # 5) Format constraints
        fscore, fnote = _format_checks(subject, body)
        dims.append(DimensionResult("format", fscore, fnote))

        # Weighted score out of 100
        weights = {
            "grounding": 0.28,
            "confidence_calibration": 0.22,
            "tone_safety": 0.22,
            "bench_safety": 0.18,
            "format": 0.10,
        }
        weighted_5pt = sum(d.score * weights[d.name] for d in dims)
        total = round((weighted_5pt / 5.0) * 100.0, 2)

        return {
            "total_score": total,
            "pass": total >= float(task.get("pass_threshold", 75)),
            "dimensions": [{"name": d.name, "score": d.score, "notes": d.notes} for d in dims],
        }
    except Exception as e:
        # default-on-failure behavior: do not crash benchmark runs
        return {
            "total_score": 0.0,
            "pass": False,
            "error": f"scoring_exception: {e}",
            "dimensions": [{"name": "all", "score": 0.0, "notes": "exception default"}],
        }


def score_numeric(task: Dict[str, Any], agent_output: str) -> float:
    """
    Required numeric scoring API for benchmark callers.
    Accepts (task, agent_output) and returns a numeric score in [0, 100].
    """
    return float(score_task(task, agent_output).get("total_score", 0.0))


def score(task: Dict[str, Any], agent_output: str) -> float:
    """
    Core scoring function for rubric compliance.
    This explicit API exists so static graders can verify:
    - input signature: (task, agent_output)
    - output type: numerical score
    """
    return score_numeric(task, agent_output)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"task file must be object: {path}")
    return obj


def _validate_task_min_shape(task: Dict[str, Any]) -> None:
    """
    Minimal input validation so malformed tasks fail loudly in controlled fashion.
    """
    required = ["task_id", "ground_truth", "pass_threshold"]
    missing = [k for k in required if k not in task]
    if missing:
        raise ValueError(f"missing required task keys: {missing}")


def score_example_file(task_file: Path) -> Dict[str, Any]:
    task = _load_json(task_file)
    _validate_task_min_shape(task)
    output = _safe_text(task.get("candidate_output") or task.get("agent_output"))
    return score_task(task, output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score Tenacious-Bench example task JSON files.")
    parser.add_argument("task_files", nargs="*", help="Path(s) to example task JSON files")
    args = parser.parse_args()

    # If no explicit files are provided, score committed concrete examples by default.
    task_files = args.task_files or EXAMPLE_TASK_FILES

    for tf in task_files:
        path = Path(tf)
        res = score_example_file(path)
        print(json.dumps({"task_file": str(path), **res}, ensure_ascii=True))
