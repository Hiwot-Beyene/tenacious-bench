# Synthesis Memo: LLM-as-a-Judge Survey (Gu et al.)

## Paper design choice I disagree with

I disagree with the common recommendation pattern of a dominant scalar judge score as the primary decision signal for evaluation throughput. Even when rubric prompts are detailed, a single scalar score is too lossy for sales-policy enforcement because different failure dimensions carry very different business costs.

## Why this matters in my Week 10 evidence

Week 10 traces show that pipeline success and business-safe behavior are separable. In traces like `add91ecb-273a-4a51-a95f-a139486bdb40` and `b8b91ec7-6722-4bf4-bedb-3303dbdda563`, enrichment completion is high, but those checkpoints do not isolate whether outputs would violate confidence calibration or bench-commitment rules later.

Probe-level evidence makes this explicit:
- `ADV-BNC-01` / `ADV-BNC-04` (capacity over-commitment) can be fluent and persuasive yet operationally disqualifying.
- `ADV-TON-02` / `ADV-TON-05` (banned language / emoji) may appear minor to a scalar quality judge but are strict brand constraints.
- `ADV-GAP-03` (condescending CTO framing) is subtle and may pass generic helpfulness while failing stakeholder-safety.

A scalar judge can average these into a misleading “acceptable” score.

## My alternative for Week 11

I use a **decomposed mechanical+judge hybrid**:
1. Mechanical hard checks (banned phrases, required signal mention, subject/length constraints, weak-signal ask-vs-assert rules).
2. Dimension-wise scores (grounding, confidence calibration, tone safety, bench safety, format) with explicit weights.
3. Pass/fail threshold on total score only after no disqualifying hard-check violations.

This structure is implemented in `evaluation/scoring_evaluator.py` and is intentionally inspectable in source code. The model-judge role is bounded to places where deterministic parsing is insufficient, reducing silent preference leakage.

## Practical takeaway

For Tenacious-style evaluation, the right judge is not “better scalar scoring”; it is enforceable dimensional decomposition with explicit failure semantics. My disagreement is therefore not with LLM-as-a-judge itself, but with score compression as the default product interface. In this domain, compression hides risk.

## Counterargument and why mine still wins here

A reasonable counterargument is that a single scalar judge score is faster to operate, easier to compare across experiments, and often correlates with human preference in aggregate. That argument is valid for throughput-oriented evaluation dashboards.

For Tenacious-style sales policy enforcement, aggregate correlation is not enough. The business cost is asymmetric: one bench-overcommitment or one condescending stakeholder framing can be disqualifying even if overall writing quality is high. My Week 10 probe and trace evidence indicates these dimensions can fail independently, so dimension-level visibility is required. In this domain, interpretable decomposition provides better risk control than scalar convenience.
