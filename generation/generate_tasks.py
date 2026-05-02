"""Optional OpenRouter bulk synthesis (Week 11 extension).

The committed v0.1 evaluation corpus is **not** produced by this module. It is built
deterministically from real company seeds (Crunchbase ODM + Conversion Engine
workspaces) and a scenario library:

  python scripts/build_corpus.py

See `bench_corpus/scenarios.py` for edge-case templates and `generation/routing_policy.md`
for model rotation when you add LLM-generated candidates.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List

from generation.model_routing import pick_bulk_generator


def pick_generator(i: int) -> str:
    return pick_bulk_generator(i)


def synthesize_placeholder(seed: int, count: int) -> List[Dict]:
    rnd = random.Random(seed)
    out = []
    for i in range(count):
        out.append(
            {
                "task_id": f"syn_{i:04d}",
                "source_mode": "multi_llm_synthesis",
                "generator_model": pick_generator(i),
                "difficulty": rnd.choice(["easy", "medium", "hard"]),
                "task": {"prompt": "TODO: wire OpenRouter + judge_filter for new candidates"},
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Placeholder OpenRouter synthesis CLI — use scripts/build_corpus.py for v0.1 shards.",
    )
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
