"""Shared logic to build Path B preference rows from a list of tasks (train or held-out eval)."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set

from bench_corpus.critic_prompt import build_critic_prompt
from bench_corpus.preference_mutators import (
    finalize_rejected_below_threshold,
    iter_mutators_for_dimension,
)
from evaluation.scoring_evaluator import score_task


def _dim_map(res: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for d in res.get("dimensions") or []:
        out[str(d["name"])] = float(d["score"])
    return out


def iter_preference_records_for_tasks(
    tasks: Iterable[Dict[str, Any]],
    *,
    allowed_mutator_ids: Optional[Set[str]] = None,
    max_pairs_per_task: int = 0,
) -> Iterable[Dict[str, Any]]:
    """
    Yield preference dicts aligned with `training_data/preferences.jsonl` schema (without schema_version).
    Caller adds partition-specific metadata.
    """
    per_task: Dict[str, int] = {}
    for task in tasks:
        chosen = task.get("candidate_output") or ""
        cr = score_task(task, chosen)
        if cr.get("error"):
            continue
        if not cr.get("pass"):
            continue
        prompt = build_critic_prompt(task)
        chosen_scores = _dim_map(cr)
        threshold = float(task.get("pass_threshold", 75))
        fd = str(task.get("failure_dimension") or "")
        tid = str(task.get("task_id"))

        for _mid, mut_fn in iter_mutators_for_dimension(fd, allowed_ids=allowed_mutator_ids):
            if max_pairs_per_task and per_task.get(tid, 0) >= max_pairs_per_task:
                break
            out = mut_fn(task, chosen)
            if not out:
                continue
            rejected_base, emitted_mut_id, target_dim = out
            rejected = finalize_rejected_below_threshold(task, rejected_base, target_dimension=target_dim)
            if not rejected:
                continue
            rr = score_task(task, rejected)
            if rr.get("pass"):
                continue

            rec: Dict[str, Any] = {
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "source_task_id": task.get("task_id"),
                "failure_dimension": fd,
                "source_mode": task.get("source_mode"),
                "rejected_mutator_id": emitted_mut_id,
                "target_violation_dimension": target_dim,
                "evaluator_pass_chosen": True,
                "evaluator_pass_rejected": False,
                "evaluator_total_score_chosen": cr.get("total_score"),
                "evaluator_total_score_rejected": rr.get("total_score"),
                "evaluator_scores_chosen": chosen_scores,
                "evaluator_scores_rejected": _dim_map(rr),
                "pass_threshold": threshold,
            }
            per_task[tid] = per_task.get(tid, 0) + 1
            yield rec
