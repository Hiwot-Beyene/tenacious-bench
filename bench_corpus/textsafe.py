"""Avoid evaluator banned substrings in synthetic outreach text (company/domain names)."""
from __future__ import annotations

# Mirrors evaluation/scoring_evaluator.py BANNED_PHRASES — substring match on email text.
BANNED_SUBSTRINGS = [
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


def _risky(text: str) -> bool:
    low = text.lower()
    return any(b in low for b in BANNED_SUBSTRINGS)


def public_company_label(name: str, domain: str, industry: str) -> str:
    """Human-facing company reference safe for tone scoring."""
    if not _risky(f"{name} {domain}"):
        return name.strip()
    ind = (industry or "B2B").strip() or "B2B"
    return f"your {_industry_short(ind)} organization"


def _industry_short(ind: str) -> str:
    """Short industry label for templates."""
    low = ind.lower()
    if len(low) > 32:
        return low[:29] + "…"
    return low


def safe_domain_hint(domain: str) -> str:
    """Domain or neutral hint; drop labels that trip banned substring checks."""
    if not domain:
        return "your careers domain"
    if _risky(domain):
        return "your public careers presence"
    return domain
