#!/usr/bin/env python3
"""
Verify Act V artifacts exist and (optionally) that publication URLs are filled.

Exit 0 = all checks passed; non-zero = missing required files or invalid JSON.

Usage:
  cd tenacious-bench
  uv run python scripts/verify_act_v_deliverables.py
  uv run python scripts/verify_act_v_deliverables.py --strict-urls
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_http_url(s: Any) -> bool:
    if not isinstance(s, str) or not s.strip():
        return False
    u = urlparse(s)
    return u.scheme in ("http", "https") and bool(u.netloc)


def _collect_null_urls(obj: Any, prefix: str = "") -> List[str]:
    missing: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if k in ("url", "pdf_url") and v is None:
                missing.append(key)
            elif isinstance(v, dict):
                missing.extend(_collect_null_urls(v, key))
            elif isinstance(v, list) and k == "community_engagement":
                for i, item in enumerate(v):
                    if isinstance(item, dict) and item.get("url") is None:
                        missing.append(f"{key}[{i}].url")
    return missing


def main() -> None:
    ap = argparse.ArgumentParser(description="Act V deliverable verification.")
    ap.add_argument(
        "--strict-urls",
        action="store_true",
        help="Fail if act_v_urls.json still has null url/pdf_url fields (use before final submission).",
    )
    ap.add_argument(
        "--require-evidence-graph",
        action="store_true",
        help="Require reports/evidence_graph.json to exist (run emit_evidence_graph.py first).",
    )
    ap.add_argument(
        "--require-community-url",
        action="store_true",
        help="Require at least one community_engagement[].url in act_v_urls.json (http(s)).",
    )
    args = ap.parse_args()

    errors: List[str] = []
    warnings: List[str] = []

    required_files = [
        REPO_ROOT / "memo.pdf",
        REPO_ROOT / "docs" / "act_v_blog_post.md",
        REPO_ROOT / "docs" / "act_v_executive_memo.md",
        REPO_ROOT / "docs" / "act_v_community_issue_template.md",
        REPO_ROOT / "publication" / "hf_dataset" / "README.md",
        REPO_ROOT / "publication" / "hf_model_adapter" / "README.md",
        REPO_ROOT / "reports" / "act_v_urls.json",
        REPO_ROOT / "docs" / "audit_memo.md",
        REPO_ROOT / "docs" / "datasheet.md",
        REPO_ROOT / "training_data" / "preferences.jsonl",
        REPO_ROOT / "training_data" / "manifest.json",
    ]
    for p in required_files:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(REPO_ROOT)}")

    urls_path = REPO_ROOT / "reports" / "act_v_urls.json"
    urls: Dict[str, Any] = {}
    if urls_path.exists():
        try:
            urls = _read_json(urls_path)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {urls_path}: {e}")
            urls = {}
        if args.strict_urls:
            nulls = _collect_null_urls(urls)
            for n in nulls:
                errors.append(f"Act V URL not filled: {n}")
        else:
            nulls = _collect_null_urls(urls)
            for n in nulls:
                warnings.append(f"URL still null (fill before publish): {n}")

        def _check_nested_url(container: Any, path: str) -> None:
            if isinstance(container, dict):
                u = container.get("url")
                if u is not None and not _is_http_url(u):
                    warnings.append(f"{path}.url is not http(s): {u!r}")

        _check_nested_url(urls.get("huggingface_dataset"), "huggingface_dataset")
        _check_nested_url(urls.get("huggingface_model"), "huggingface_model")
        _check_nested_url(urls.get("blog_post"), "blog_post")
        em = urls.get("executive_memo")
        if isinstance(em, dict) and em.get("pdf_url") is not None and not _is_http_url(em.get("pdf_url")):
            warnings.append(f"executive_memo.pdf_url is not http(s): {em.get('pdf_url')!r}")

        if args.require_community_url:
            ce = urls.get("community_engagement")
            ok = False
            if isinstance(ce, list):
                for item in ce:
                    if isinstance(item, dict) and _is_http_url(item.get("url")):
                        ok = True
                        break
            if not ok:
                errors.append(
                    "act_v_urls.json: add community_engagement: [{\"type\": \"...\", \"url\": \"https://...\"}]"
                )

    eg = REPO_ROOT / "reports" / "evidence_graph.json"
    if args.require_evidence_graph:
        if not eg.exists():
            errors.append("Missing reports/evidence_graph.json — run scripts/emit_evidence_graph.py")
        else:
            try:
                _read_json(eg)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {eg}: {e}")

    ablation = REPO_ROOT / "reports" / "ablation_results.json"
    if ablation.exists():
        try:
            ab = _read_json(ablation)
            comp = ab.get("comparisons_run") or []
            if comp == ["delta_c"] or ab.get("n_pairs_input") == 0:
                warnings.append(
                    "ablation_results.json looks like delta_c-only or empty scoring; "
                    "run full: uv run python scripts/run_sealed_ablation.py"
                )
        except json.JSONDecodeError as e:
            warnings.append(f"Could not parse ablation_results.json: {e}")

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        raise SystemExit(1)
    print("Act V deliverable check OK.")


if __name__ == "__main__":
    main()
