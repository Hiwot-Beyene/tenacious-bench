"""Contamination checks for Tenacious-Bench partitions (Week 11 Act II).

Template-heavy corpora share long boilerplate across splits; naive 8-grams on full
input always collide. We therefore:

1) **Exact-input leak**: anonymized full input (brief + bench + thread + teaser) must
   not match any training row (train vs held-out, train vs dev).
2) **High-entropy 8-grams**: 8-grams on the slice that varies per task (firmographics +
   public teaser) must not overlap train→held-out union (prevents near-identical
   prospect stories leaking).
3) **Embedding proxy (cheap, linear)**: **bag-of-word** frequency vectors on the same slice;
   cosine similarity; flag held-out vs train **and** held-out vs dev pairs at or above
   ``--embedding-threshold`` (default **0.85**). This is a deliberate stand-in for a small
   sentence embedding model: it is deterministic, dependency-free, and correlates with
   lexical overlap on the high-entropy slice (see ``thresholds.embedding_methodology`` in the report).
4) **Time-shift / signal-window provenance**: rows with a **public four-digit year** in the
   brief or bench (external signal dated to a calendar year) must carry
   ``internal_capacity_snapshot.as_of`` so bench/capacity claims are anchored to a documented
   snapshot window, not an implied “current” date.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _anonymize_blob(text: str, company: str, domain: str) -> str:
    t = text or ""
    if company:
        t = t.replace(company, "<ORG>")
    if domain:
        t = t.replace(domain, "<DOM>")
    return t


def full_anonymized_input(task: Dict[str, Any]) -> str:
    ic = task.get("input_context") or {}
    p = ic.get("prospect") or {}
    company = str(p.get("company") or "")
    domain = str(p.get("domain") or "")
    parts: List[str] = []
    for key in ("hiring_signal_brief", "bench_summary", "prior_thread", "public_context_teaser"):
        parts.append(_anonymize_blob(str(ic.get(key) or ""), company, domain))
    return "\n".join(parts).lower()


def high_entropy_slice(task: Dict[str, Any]) -> str:
    """Firmographics + teaser — differs per seed company; shared templates live elsewhere."""
    ic = task.get("input_context") or {}
    p = ic.get("prospect") or {}
    bits = [
        str(p.get("company") or ""),
        str(p.get("domain") or ""),
        str(p.get("region") or ""),
        str(p.get("employees_bucket") or ""),
        str(ic.get("public_context_teaser") or ""),
    ]
    return " ".join(bits).lower()


def bow_counts(text: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for w in text.split():
        out[w] = out.get(w, 0) + 1
    return out


def cosine_bow(a: Dict[str, int], b: Dict[str, int]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def time_shift_violations(rows: List[Dict[str, Any]]) -> List[str]:
    bad: List[str] = []
    for r in rows:
        ic = r.get("input_context") or {}
        blob = (str(ic.get("hiring_signal_brief") or "") + " " + str(ic.get("bench_summary") or "")).lower()
        if not _YEAR.search(blob):
            continue
        snap = ic.get("internal_capacity_snapshot")
        if not isinstance(snap, dict) or not str(snap.get("as_of") or "").strip():
            bad.append(str(r.get("task_id")))
    return bad


def exact_duplicate_across(train_rows: List[Dict[str, Any]], other_rows: List[Dict[str, Any]]) -> List[str]:
    train_fps = {full_anonymized_input(r) for r in train_rows}
    hits: List[str] = []
    for r in other_rows:
        fp = full_anonymized_input(r)
        if fp in train_fps:
            hits.append(str(r.get("task_id")))
    return hits


def embedding_flags_against_ref(
    ref_rows: List[Dict[str, Any]],
    held_rows: List[Dict[str, Any]],
    threshold: float,
    *,
    ref_partition_label: str,
) -> Tuple[List[Dict[str, Any]], float]:
    ref_bows = [(r["task_id"], bow_counts(high_entropy_slice(r))) for r in ref_rows]
    flagged: List[Dict[str, Any]] = []
    worst = 0.0
    for hr in held_rows:
        hb = bow_counts(high_entropy_slice(hr))
        hid = hr["task_id"]
        for rid, rb in ref_bows:
            c = cosine_bow(hb, rb)
            if c > worst:
                worst = c
            if c >= threshold:
                flagged.append(
                    {
                        "held_task_id": hid,
                        f"{ref_partition_label}_task_id": rid,
                        "cosine": round(c, 6),
                    }
                )
    return flagged, worst


def run_report(
    *,
    train_path: Path,
    heldout_path: Path,
    dev_path: Path | None,
    ngram_n: int,
    embedding_threshold: float,
) -> Dict[str, Any]:
    train_rows = list(iter_jsonl(train_path))
    held_rows = list(iter_jsonl(heldout_path))
    dev_rows = list(iter_jsonl(dev_path)) if dev_path and dev_path.exists() else []

    dup_held = exact_duplicate_across(train_rows, held_rows)
    dup_dev_train = exact_duplicate_across(train_rows, dev_rows) if dev_rows else []
    dup_held_dev = exact_duplicate_across(dev_rows, held_rows) if dev_rows else []

    # n-gram check uses high-entropy slice (see module docstring).
    def slice_ngrams(text: str) -> Set[str]:
        toks = text.split()
        nn = ngram_n
        if len(toks) < nn:
            return set()
        return {" ".join(toks[i : i + nn]) for i in range(len(toks) - nn + 1)}

    train_union_he: Set[str] = set()
    for r in train_rows:
        train_union_he |= slice_ngrams(high_entropy_slice(r))
    dev_union_he: Set[str] = set()
    for r in dev_rows:
        dev_union_he |= slice_ngrams(high_entropy_slice(r))

    ngram_viol_train_held: List[str] = []
    ngram_viol_dev_held: List[str] = []
    for r in held_rows:
        he_ng = slice_ngrams(high_entropy_slice(r))
        if he_ng & train_union_he:
            ngram_viol_train_held.append(str(r.get("task_id")))
        if dev_rows and he_ng & dev_union_he:
            ngram_viol_dev_held.append(str(r.get("task_id")))

    embed_train, max_cos_train = embedding_flags_against_ref(
        train_rows, held_rows, embedding_threshold, ref_partition_label="train"
    )
    embed_dev: List[Dict[str, Any]] = []
    max_cos_dev = 0.0
    if dev_rows:
        embed_dev, max_cos_dev = embedding_flags_against_ref(
            dev_rows, held_rows, embedding_threshold, ref_partition_label="dev"
        )
    ts_held = time_shift_violations(held_rows)
    ts_dev = time_shift_violations(dev_rows) if dev_rows else []

    ok = (
        not dup_held
        and not dup_dev_train
        and not dup_held_dev
        and not ngram_viol_train_held
        and not ngram_viol_dev_held
        and not embed_train
        and not embed_dev
        and not ts_held
        and not ts_dev
    )

    return {
        "schema_version": "1.2",
        "status": "pass" if ok else "fail",
        "partition_paths": {
            "train": str(train_path),
            "heldout": str(heldout_path),
            "dev": str(dev_path) if dev_path else None,
        },
        "thresholds": {
            "ngram_n": ngram_n,
            "ngram_field": "high_entropy_slice (company, domain, region, employees_bucket, public_context_teaser)",
            "ngram_rationale": (
                f"Strict {ngram_n}-grams on full anonymized input collide on shared templates; "
                "the high-entropy slice isolates prospect-specific surface form (same slice philosophy "
                "as scripts/verify_training_data_leakage.py)."
            ),
            "embedding_cosine_max": embedding_threshold,
            "embedding_field": "high_entropy_slice",
            "embedding_methodology": (
                "Bag-of-word cosine (token counts) — cheap linear embedding proxy, no external model "
                "weights; threshold 0.85 matches verify_training_data_leakage.py. "
                "Swap for MiniLM-L6-v2 etc. only if you accept new dependencies and non-determinism."
            ),
            "time_shift_rule": (
                "If hiring_signal_brief or bench_summary contains a 19xx/20xx year, "
                "internal_capacity_snapshot.as_of must be non-empty (signal-window + bench coherence)."
            ),
        },
        "checks": {
            "exact_duplicate_train_heldout": {"violations": len(dup_held), "task_ids": dup_held},
            "exact_duplicate_train_dev": {"violations": len(dup_dev_train), "task_ids": dup_dev_train},
            "exact_duplicate_dev_heldout": {"violations": len(dup_held_dev), "task_ids": dup_held_dev},
            "ngram_high_entropy_train_heldout": {
                "violations": len(ngram_viol_train_held),
                "task_ids": ngram_viol_train_held,
            },
            "ngram_high_entropy_dev_heldout": {
                "violations": len(ngram_viol_dev_held),
                "task_ids": ngram_viol_dev_held,
            },
            "embedding_cosine_train_heldout": {
                "violations": len(embed_train),
                "max_cosine_observed": round(max_cos_train, 6),
                "pairs": embed_train[:50],
            },
            "embedding_cosine_dev_heldout": {
                "violations": len(embed_dev),
                "max_cosine_observed": round(max_cos_dev, 6),
                "pairs": embed_dev[:50],
            },
            "time_shift_heldout": {"flags": len(ts_held), "task_ids": ts_held},
            "time_shift_dev": {"flags": len(ts_dev), "task_ids": ts_dev},
        },
        "methodology_notes": (
            "Comparisons cover held-out vs training and held-out vs dev (exact, n-gram, embedding). "
            "Full-input n-grams are not primary: scenario templates repeat across splits."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Run contamination checks (train vs held-out, optional dev).")
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--train", type=Path, default=root / "data" / "tasks_train.jsonl")
    ap.add_argument("--heldout", type=Path, default=root / "data" / "tasks_heldout.jsonl")
    ap.add_argument("--dev", type=Path, default=root / "data" / "tasks_dev.jsonl")
    ap.add_argument("--out", type=Path, default=root / "reports" / "contamination_check.json")
    ap.add_argument("--ngram-n", type=int, default=8)
    ap.add_argument("--embedding-threshold", type=float, default=0.85)
    args = ap.parse_args()

    report = run_report(
        train_path=args.train,
        heldout_path=args.heldout,
        dev_path=args.dev,
        ngram_n=args.ngram_n,
        embedding_threshold=args.embedding_threshold,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "wrote": str(args.out)}, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
