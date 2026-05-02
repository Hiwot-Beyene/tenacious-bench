# Act V — Publish checklist

- **Blog:** https://hiwotbeyene.substack.com/p/what-style-benches-miss-about-b2b  
- **HF dataset / model:** see README Public artifacts table  
- **memo.pdf:** `uv sync --extra pdf && uv run python scripts/generate_memo_pdf.py`  
- **evidence_graph:** `uv run python scripts/emit_evidence_graph.py`  
- **Verify:** `uv run python scripts/verify_act_v_deliverables.py --strict-urls --require-evidence-graph --require-community-url`
