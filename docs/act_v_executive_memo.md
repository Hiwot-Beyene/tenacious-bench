# Executive Memo — Tenacious-Bench Week 11 (Acts IV–V)

**To:** CEO, CFO, Engineering leadership  
**From:** Hiwot Beyene — Tenacious-Bench / Week 11  
**Date:** (update on publish)  
**Subject:** Path B critic shipped to Hub; evidence package; risks and asks

## Bottom line

We completed a **reproducible Path B training pipeline** (DPO + LoRA on Tenacious preferences) and an **auditable held-out ablation harness** aligned to the Week 11 brief. Public **Act V** deliverables are **dataset + optional adapter** on Hugging Face, a **technical blog post**, **community engagement** (τ² comparison), and a machine-readable **`evidence_graph.json`** linking artifacts to URLs.

## Business value

- **Evaluator + critic** reduce risk from “fluent but wrong” outbound copy: calibration, commitment safety, tone, overrides, gap framing.
- **Open publication** supports recruiting, vendor diligence, and partnership trust without exposing proprietary prompts beyond committed rubrics.

## What we published (checklist)

| Item | Status | Location / action |
|------|--------|-------------------|
| HF dataset | Fill URL in `reports/act_v_urls.json` | `publication/hf_dataset/README.md` |
| HF adapter (optional) | Fill URL | `publication/hf_model_adapter/README.md` |
| Blog | Fill URL | `docs/act_v_blog_post.md` → your CMS |
| Community post / issue | Fill URL | `docs/act_v_community_issue_template.md` |
| Evidence graph | Regenerate after URLs | `uv run python scripts/emit_evidence_graph.py` |

## Results (update after full ablation)

- **Delta A / B:** paste mean Δ accuracy, 95% CI, *p*-values from `reports/ablation_results.json`.
- **Delta C (τ²):** informational Week 10 reference only unless policy approves a re-run budget.
- **Cost–Pareto:** confirm latency/token deltas are acceptable for production inference.

## Risks

1. **Slice metrics ≠ revenue** — preference accuracy is a **proxy**; A/B on real pipelines still required.
2. **Non-significant first runs** — may indicate data scale or task mismatch; not a reason to hide CIs.
3. **License / data** — Hub upload must exclude secrets; legal review of `company_seeds.json` exposure.

## Asks

1. **Legal/comms sign-off** on public dataset card wording and blog.
2. **Archive** a snapshot (Zenodo or HF revision) if we need a frozen citation for customers.
3. **Budget** for optional full τ² or production A/B follow-on if Delta A/B justify it.

---

## PDF deliverable (`memo.pdf`)

Week 11 **final submission** requires **`memo.pdf`** (two pages: decision + skeptic’s appendix). Generate from the repo:

```bash
cd tenacious-bench
uv sync --extra pdf
uv run python scripts/generate_memo_pdf.py
```

This writes **`memo.pdf`** at the repository root. Re-run after `reports/ablation_results.json` is updated from a full sealed ablation. For public hosting of the same file, upload to Drive/GitHub Releases and set `executive_memo.pdf_url` in `reports/act_v_urls.json`.
