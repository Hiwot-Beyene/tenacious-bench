"""Named model families and rotation rules (Week 11 rubric: anti–preference-leakage).

Roles:
- **Frontier seed author** — rare, high-quality scenario seeds (eval-tier family).
- **Dev-tier bulk generator** — high-volume task body / synthesis (cheap OpenRouter IDs).
- **Dev-tier judge** — pointwise filter on bulk stream; **must differ** from the bulk generator id.
- **Eval-tier judge** — spot-check calibration only (~50 tasks), distinct family from bulk generators.

See `docs/methodology.md` (Li et al., 2025) and `generation/routing_policy.md`.
"""
from __future__ import annotations

# Role: frontier seed / scenario authoring (small budget; not used in deterministic v0.1 build).
FRONTIER_SEED_AUTHOR_MODEL = "anthropic/claude-sonnet-4.6"

# Role: dev-tier bulk synthesis rotation (OpenRouter model ids).
DEV_TIER_BULK_GENERATORS = (
    "qwen/qwen3-next-80b-a3b-instruct",
    "deepseek/deepseek-chat",
)

# Tasks built only from `scenario_catalog.py` + company seeds (no LLM author for the row body).
DETERMINISTIC_CATALOG_AUTHOR = "deterministic/v0.1-scenario-catalog"

# Role: eval-tier judge — **only** for the fixed calibration subset in `run_judge_filter_pipeline.py`.
EVAL_TIER_CALIBRATION_JUDGE = "openai/gpt-5"


def pick_bulk_generator(seq: int) -> str:
    """Round-robin dev-tier bulk generator (deterministic)."""
    return DEV_TIER_BULK_GENERATORS[seq % len(DEV_TIER_BULK_GENERATORS)]


def dev_judge_for_bulk_generator(generator_model_id: str) -> str:
    """
    Dev-tier judge: **different** OpenRouter model id than the bulk generator.
    Same underlying vendor is allowed; ids must differ (operational separation).
    """
    g = (generator_model_id or "").lower()
    if "qwen" in g:
        return DEV_TIER_BULK_GENERATORS[1]
    if "deepseek" in g:
        return DEV_TIER_BULK_GENERATORS[0]
    # Catalog / unknown author → fix judge to first dev-tier id (generator is not an LLM).
    return DEV_TIER_BULK_GENERATORS[0]


def effective_author_model(task: dict) -> str:
    """Model id (or catalog stub) that conceptually *authored* the candidate output."""
    sm = task.get("source_mode") or ""
    if sm == "multi_llm_synthesis":
        route = task.get("synthesis_route")
        if isinstance(route, str) and route.strip():
            return route.strip()
        # Fallback: derive from task_id suffix
        tid = str(task.get("task_id") or "tb_v01_0")
        try:
            seq = int(tid.split("_")[-1])
        except ValueError:
            seq = 0
        return pick_bulk_generator(seq)
    return DETERMINISTIC_CATALOG_AUTHOR
