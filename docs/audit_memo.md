# Audit Memo: What Public Benches Miss for Tenacious

Public benchmarks (including retail-style dialog benchmarks) under-grade Tenacious-critical behavior because they reward task completion, not policy-safe sales reasoning in low-confidence B2B contexts. Week 10 evidence shows five distinct gaps.

## Gap 1: Confidence calibration under weak hiring signal (non-obvious)

Public benches usually score whether an answer is coherent and helpful, but do not grade whether confidence language matches signal strength. In Tenacious outreach, weak signal must trigger “ask, do not assert.” Week 10 probes explicitly target this (`ADV-SIG-01`, `ADV-SIG-02`, `ADV-SIG-03`, `ADV-SIG-04`), and we observed outputs that required post-hoc guardrails to avoid over-assertion. In traces, enrich cycles show mechanically valid briefs but no direct confidence-aware penalty in score (`trace_id=fd689eca-367e-4419-83fa-c9a9ea5654cb`, `trace_id=7b41bd5a-0ddb-4ea6-b893-ef7309662fb1`, `trace_id=da59fe57-0fbc-4462-86e8-ffeeb72678a3`). This is non-obvious because outputs can look fluent while still being decision-unsafe for real outreach.

## Gap 2: Bench commitment safety vs. fluent persuasion

Retail public benchmarks do not grade contractual risk from staffing claims. Tenacious must not promise unavailable stack/capacity. Probe evidence (`ADV-BNC-01`, `ADV-BNC-02`, `ADV-BNC-04`) shows this as a first-order failure mode. Traces demonstrate that enrichment can pass schema checks without proving commitment safety (`trace_id=add91ecb-273a-4a51-a95f-a139486bdb40`, `trace_id=b8b91ec7-6722-4bf4-bedb-3303dbdda563`). Public benchmarks would often score these as “good responses” if language is polished, while Tenacious business risk is high.

## Gap 3: Tone-marker compliance as hard constraints, not style preference

Tenacious requires strict marker compliance (Direct, Grounded, Honest, Professional, Non-condescending) plus banned lexicon checks. This is not captured by general “helpfulness” grades. Probe set (`ADV-TON-01`, `ADV-TON-02`, `ADV-TON-03`, `ADV-TON-04`, `ADV-TON-05`, `ADV-BNC-03`) shows recurrent failure risk. Week 10 traces show successful orchestration events where only later policy layers enforce brand quality (`trace_id=3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95`, `trace_id=85724927-681b-47b5-ba65-a13d705084c6`). Public benches underweight this because they do not model enterprise brand harm from one “technically correct” but off-voice email.

## Gap 4: Multi-system coordination and override obedience

Tenacious operations require agent obedience to CRM/human overrides and sequence-state coordination. Public dialog benchmarks rarely include CRM state conflicts. Probes (`ADV-DUL-01`, `ADV-DUL-02`, `ADV-MLT-01`, `ADV-MLT-02`) define failures where automation continues despite do-not-send or thread-level context. In Week 10 traces, downstream workflow events (`trace_id=de6edd34-0276-41b9-88d8-87a1956d65ef`, `trace_id=91412980-6b88-4fd5-81d5-b37430c3a531`, `trace_id=ac32ab98-d962-4f05-983e-7a7d5ecb555a`) confirm pipeline progression, but no benchmark-level metric yet separates “workflow success” from “override-safe behavior.”

## Gap 5: Evidence-linked gap framing vs. condescension risk

Public benchmarks do not penalize subtle condescension in competitor-gap language. Tenacious requires framing gaps as hypotheses/questions, never as leadership failure. Probe evidence (`ADV-GAP-01`, `ADV-GAP-02`, `ADV-GAP-03`, `ADV-GAP-04`) shows this is distinct from generic tone. In Week 10, enrichment quality and compose success can still coexist with this risk (`trace_id=0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac`, `trace_id=6f232df2-44c6-442b-8b6c-74e302e72aa9`). Public benches miss this because they grade surface politeness, not stakeholder-status-aware framing.

## Conclusion

The central gap is not language generation quality alone; it is policy-consistent decision quality under uncertain evidence. Tenacious-Bench should therefore prioritize critic-style scoring on confidence calibration, commitment safety, override obedience, and evidence-linked non-condescending framing.
