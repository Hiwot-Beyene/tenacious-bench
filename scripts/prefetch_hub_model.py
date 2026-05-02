#!/usr/bin/env python3
"""Download a Hugging Face model snapshot once so training starts without long Hub waits.

Uses the same HF_HOME / token behavior as training (loads tenacious-bench/.env).

Example:
  cd tenacious-bench
  uv sync --extra train
  uv run python scripts/prefetch_hub_model.py --model-id Qwen/Qwen2.5-0.5B-Instruct --cache-root outputs/shared_hf_cache

Then point training at that cache:
  export HF_HOME=$(pwd)/outputs/shared_hf_cache
  uv run python training/preference_lora_train.py --output-dir outputs/preference_lora_run1
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def main() -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as e:
        raise SystemExit(
            "Install train extras: cd tenacious-bench && uv sync --extra train\n" f"{e}"
        ) from e

    ap = argparse.ArgumentParser(description="Prefetch a Hub model into HF_HOME.")
    ap.add_argument("--model-id", type=str, required=True, help="e.g. Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument(
        "--cache-root",
        type=Path,
        default=None,
        help="Directory to use as HF_HOME for this download (created if missing). "
        "Default: outputs/hf_prefetch_cache under repo.",
    )
    args = ap.parse_args()

    cache_root = args.cache_root or (REPO_ROOT / "outputs" / "hf_prefetch_cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_root.resolve())

    print(f"HF_HOME={os.environ['HF_HOME']}")
    print(f"Downloading snapshot for {args.model_id} ...")
    path = snapshot_download(repo_id=args.model_id)
    print(f"Done. Snapshot at: {path}")
    print(
        "For training, run with the same HF_HOME, e.g.:\n"
        f"  export HF_HOME={os.environ['HF_HOME']}\n"
        "  uv run python training/preference_lora_train.py --output-dir outputs/your_run"
    )


if __name__ == "__main__":
    main()
