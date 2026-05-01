"""Load and cache real company rows (Crunchbase ODM + Conversion Engine workspaces)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]


def monorepo_root(tenacious_bench_root: Path) -> Path:
    return tenacious_bench_root.parent


def default_paths(tenacious_bench_root: Path) -> Dict[str, Path]:
    m = monorepo_root(tenacious_bench_root)
    return {
        "crunchbase": m / "conversion-engine" / "data" / "crunchbase-companies-information.json",
        "workspaces": m / "conversion-engine" / "data" / "runtime" / "workspaces.json",
        "traces": m / "conversion-engine" / "eval" / "agent_trace_log.jsonl",
        "seeds_out": tenacious_bench_root / "data" / "company_seeds.json",
    }


def _domain_from_website(url: str) -> str:
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return netloc[4:] if netloc.startswith("www.") else netloc


def _primary_industry(row: Dict[str, Any]) -> str:
    inds = row.get("industries") or []
    if inds and isinstance(inds, list) and isinstance(inds[0], dict):
        return str(inds[0].get("value") or inds[0].get("id") or "B2B")
    return "B2B"


def _teaser(about: Any, limit: int = 100) -> str:
    if not about:
        return ""
    s = re.sub(r"\s+", " ", str(about)).strip()
    return s[:limit] + ("…" if len(s) > limit else "")


def build_seeds_from_sources(
    crunchbase_path: Path,
    workspaces_path: Optional[Path],
    min_count: int = 320,
) -> List[Dict[str, Any]]:
    raw = json.loads(crunchbase_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("crunchbase JSON must be a list")

    by_domain: Dict[str, Dict[str, Any]] = {}
    for row in raw:
        name = str(row.get("name") or "").strip()
        website = str(row.get("website") or "").strip()
        if not name or not website:
            continue
        domain = _domain_from_website(website)
        if not domain or domain in by_domain:
            continue
        by_domain[domain] = {
            "name": name,
            "domain": domain,
            "website": website,
            "segment_hint": _primary_industry(row),
            "region": str(row.get("region") or row.get("country_code") or "unknown"),
            "employees_bucket": str(row.get("num_employees") or "unknown"),
            "industry_primary": _primary_industry(row),
            "about_teaser": _teaser(row.get("about") or row.get("full_description")),
            "founded_date": str(row.get("founded_date") or ""),
            "source": "crunchbase_odm",
            "external_id": str(row.get("id") or row.get("uuid") or domain),
        }

    if workspaces_path and workspaces_path.exists():
        ws = json.loads(workspaces_path.read_text(encoding="utf-8"))
        if isinstance(ws, dict):
            for slug, payload in ws.items():
                if not isinstance(payload, dict):
                    continue
                dn = str(payload.get("domain") or "").strip().lower()
                name = str(payload.get("company_name") or slug).strip()
                if not dn:
                    continue
                row = {
                    "name": name,
                    "domain": dn,
                    "website": f"https://{dn}",
                    "segment_hint": str(
                        (payload.get("brief") or {}).get("signals", {})
                        .get("job_velocity", {})
                        .get("label", "workspace_seed")
                    ),
                    "region": "workspace_runtime",
                    "employees_bucket": "unknown",
                    "industry_primary": "conversion_engine_workspace",
                    "about_teaser": _teaser((payload.get("brief") or {}).get("summary", ""), 120),
                    "founded_date": "",
                    "source": "conversion_engine_workspace",
                    "external_id": slug,
                }
                # Workspace rows win on collision for trace realism.
                by_domain[dn] = row

    seeds = sorted(by_domain.values(), key=lambda x: (x["name"].lower(), x["domain"]))
    if len(seeds) < min_count:
        raise ValueError(f"need at least {min_count} unique domain seeds, got {len(seeds)}")
    return seeds


def load_trace_anchors(traces_path: Path) -> List[Tuple[str, str]]:
    if not traces_path.exists():
        return []
    out: List[Tuple[str, str]] = []
    seen = set()
    with traces_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tid = str(obj.get("trace_id") or "")
            lead = str(obj.get("lead_id") or "")
            if tid and lead and (tid, lead) not in seen:
                seen.add((tid, lead))
                out.append((tid, lead))
    return out


def ensure_company_seeds(
    tenacious_bench_root: Path,
    *,
    crunchbase_path: Optional[Path] = None,
    workspaces_path: Optional[Path] = None,
    write: bool = False,
) -> List[Dict[str, Any]]:
    paths = default_paths(tenacious_bench_root)
    seeds_path = paths["seeds_out"]
    if seeds_path.exists() and not write:
        data = json.loads(seeds_path.read_text(encoding="utf-8"))
        if isinstance(data, list) and len(data) >= 240:
            return data

    cb = crunchbase_path or paths["crunchbase"]
    if not cb.exists():
        raise FileNotFoundError(
            f"Missing Crunchbase ODM export at {cb}. Restore conversion-engine data or pass --crunchbase."
        )
    ws = workspaces_path if workspaces_path is not None else paths["workspaces"]
    seeds = build_seeds_from_sources(cb, ws if ws.exists() else None)
    seeds_path.parent.mkdir(parents=True, exist_ok=True)
    seeds_path.write_text(json.dumps(seeds, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return seeds
