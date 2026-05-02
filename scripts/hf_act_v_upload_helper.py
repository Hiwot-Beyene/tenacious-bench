#!/usr/bin/env python3
"""
Print vetted Hugging Face Hub commands for Act V uploads (dataset + optional adapter).

Does not require huggingface_hub at import time. Run after `hf auth login` (or `HF_TOKEN`).

Uses the modern **`hf`** CLI. The old `huggingface-cli` command is deprecated or missing in some envs;
if `hf` is not found, run: `uv sync --extra publish` then `uv run hf --help`.

Usage:
  cd tenacious-bench
  uv run python scripts/hf_act_v_upload_helper.py --hf-user YOUR_USER
  uv run python scripts/hf_act_v_upload_helper.py --hf-user YOUR_USER --dataset-repo tenacious-bench-v01 --execute-dataset-card

**This script only PRINTS commands** (it does not run `hf upload` for you). Copy each line into your
terminal, or use `--execute-dataset-card` / `--execute-model-card` to upload **README.md only** via API.

Match `--dataset-repo` / `--model-repo` to repos that already exist on your Hub (defaults: `tenacious-bench-v0.1`, `tenacious-bench-lora`).
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _maybe_upload_readme(repo_id: str, readme: Path, *, repo_type: str) -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError as e:
        raise SystemExit(
            "Install publish extras: uv sync --extra publish\n" + str(e)
        ) from e
    api = HfApi()
    api.upload_file(
        path_or_fileobj=str(readme),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type=repo_type,
        commit_message="Act V: dataset/model card from tenacious-bench publication/",
    )
    print(f"Uploaded README.md to {repo_type}/{repo_id}")


def main() -> None:
    ap = argparse.ArgumentParser(description="HF upload helper for Act V.")
    ap.add_argument("--hf-user", type=str, required=True, help="Your Hugging Face username or org")
    ap.add_argument(
        "--dataset-repo",
        type=str,
        default="tenacious-bench-v0.1",
        help="Dataset repo name (without user); must match existing Hub repo, e.g. tenacious-bench-v0.1",
    )
    ap.add_argument(
        "--model-repo",
        type=str,
        default="tenacious-bench-lora",
        help="Model/adapter repo name (without user), e.g. tenacious-bench-lora",
    )
    ap.add_argument(
        "--execute-dataset-card",
        action="store_true",
        help="Upload publication/hf_dataset/README.md via huggingface_hub (requires auth).",
    )
    ap.add_argument(
        "--execute-model-card",
        action="store_true",
        help="Upload publication/hf_model_adapter/README.md via huggingface_hub (requires auth).",
    )
    args = ap.parse_args()

    ds_id = f"{args.hf_user}/{args.dataset_repo}"
    m_id = f"{args.hf_user}/{args.model_repo}"
    ds_readme = REPO_ROOT / "publication" / "hf_dataset" / "README.md"
    m_readme = REPO_ROOT / "publication" / "hf_model_adapter" / "README.md"

    print(
        "\n"
        "******************************************************************************\n"
        "*  THIS SCRIPT ONLY PRINTS COMMANDS — it does not upload to Hugging Face.   *\n"
        "*  Copy each `hf upload ...` line into your terminal and run it.           *\n"
        "*  Repos used: "
        f"{ds_id} (dataset), {m_id} (model). Override with --dataset-repo / --model-repo.\n"
        "*  README-only upload: add --execute-dataset-card and/or --execute-model-card.\n"
        "******************************************************************************\n"
    )

    print("=== 0) Auth (once per machine) ===\n")
    print("hf auth login\n")
    print("# If `hf` is not found: uv sync --extra publish && uv run hf auth login\n")

    print("=== 1) Create repos (SKIP if they already exist on huggingface.co) ===\n")
    print(
        f"hf repos create {ds_id} --repo-type dataset --exist-ok\n"
        f"hf repos create {m_id} --repo-type model --exist-ok\n"
        f"# If you see 'already exists', that is fine — go to section 2.\n"
    )

    print("=== 2) Upload dataset shards (from tenacious-bench/) ===\n")
    print(
        f"hf upload {ds_id} data/tasks_all.jsonl tasks_all.jsonl --repo-type dataset\n"
        f"hf upload {ds_id} data/tasks_train.jsonl tasks_train.jsonl --repo-type dataset\n"
        f"hf upload {ds_id} data/tasks_dev.jsonl tasks_dev.jsonl --repo-type dataset\n"
        f"hf upload {ds_id} data/tasks_heldout.jsonl tasks_heldout.jsonl --repo-type dataset\n"
        f"hf upload {ds_id} training_data/preferences.jsonl training_data/preferences.jsonl --repo-type dataset\n"
        f"hf upload {ds_id} training_data/manifest.json training_data/manifest.json --repo-type dataset\n"
        f"hf upload {ds_id} schema.json schema.json --repo-type dataset\n"
    )

    print("=== 3) Upload LoRA adapter weights ===\n")
    print(
        f"# Directory must include adapter_model.safetensors (or .bin):\n"
        f"hf upload {m_id} outputs/preference_lora_day5/lora_adapter . --repo-type model\n"
    )

    print("=== 4) Cards ===\n")
    print(f"Source dataset card: {ds_readme.relative_to(REPO_ROOT)}")
    print(f"Source model card:   {m_readme.relative_to(REPO_ROOT)}\n")

    if args.execute_dataset_card:
        if not ds_readme.is_file():
            raise SystemExit(f"missing {ds_readme}")
        _maybe_upload_readme(ds_id, ds_readme, repo_type="dataset")
    if args.execute_model_card:
        if not m_readme.is_file():
            raise SystemExit(f"missing {m_readme}")
        _maybe_upload_readme(m_id, m_readme, repo_type="model")

    print("\n=== 5) After publish: fill reports/act_v_urls.json and run ===\n")
    print("uv run python scripts/emit_evidence_graph.py")
    print("uv run python scripts/verify_act_v_deliverables.py --strict-urls --require-evidence-graph --require-community-url")


if __name__ == "__main__":
    main()
