"""Task synthesis orchestrator (interim scaffold).

Intended run shape:
- load seed traces/probes
- route generation across cheap-tier models with deterministic seed
- emit raw task candidates to JSONL
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List

CHEAP_MODELS = [
    # Qwen: good cost/quality for bulk structured generation.
    "qwen/qwen3-next-80b-a3b-instruct",
    # DeepSeek: different model family improves diversity and supports rotation.
    "deepseek/deepseek-chat",
]


def pick_generator(i: int) -> str:
    # Deterministic round-robin keeps runs reproducible and balanced by family.
    return CHEAP_MODELS[i % len(CHEAP_MODELS)]


def synthesize_placeholder(seed: int, count: int) -> List[Dict]:
    # Local RNG prevents global-random side effects and preserves exact reruns.
    rnd = random.Random(seed)
    out = []
    for i in range(count):
        out.append(
            {
                "task_id": f"syn_{i:04d}",
                "source_mode": "multi_llm_synthesis",
                "generator_model": pick_generator(i),
                "difficulty": rnd.choice(["easy", "medium", "hard"]),
                "task": {"prompt": "TODO: generated task"},
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--seed", type=int, default=11711)
    args = ap.parse_args()

    rows = synthesize_placeholder(args.seed, args.count)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
