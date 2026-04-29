# Synthesis Memo: Liu et al. (COLM 2024) — Synthetic Data Best Practices

## Paper design choice I disagree with

I disagree with the practical emphasis (in deployment interpretation) on scaling synthetic volume once quality filters are in place. The paper correctly stresses quality controls, but in Tenacious-style sales evaluation, increasing synthetic volume too early still amplifies the wrong failures because weak-signal tasks are distributionally rare and easy to flatten into generic wording.

## Why this matters in my Week 10 evidence

In my Week 10 logs, the worst business-risk outputs were not random low-quality generations; they were fluent outputs with subtle policy failures. For example, traces such as `3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95` and `85724927-681b-47b5-ba65-a13d705084c6` show successful enrichment and compose calls while still requiring strict policy/tone constraints downstream. If I expand synthetic volume before preserving these edge-case constraints, I get more fluent-but-miscalibrated examples, not better supervision.

Probe evidence aligns with this concern. `ADV-SIG-01`, `ADV-SIG-03`, and `ADV-SIG-04` target weak-signal over-assertion; these are exactly the examples that disappear in naive synthetic expansion because template generators overproduce high-confidence framing. Likewise `ADV-BNC-02` and `ADV-GAP-03` are narrow, high-impact behaviors that volume-first generation tends to under-sample.

## My alternative for Week 11

I am using a **constraint-first synthesis policy**:
1. Lock failure dimensions from Week 10 probes/taxonomy.
2. Enforce critic-gradeable fields before accepting any candidate task.
3. Scale volume only inside each failure bucket after bucket coverage is met.

This keeps synthetic growth tied to diagnostic coverage rather than language diversity alone. Concretely, I set fixed source-mode and failure-dimension quotas in the datasheet (240 tasks with explicit splits) and require pointwise judge thresholds on verifiability and rubric clarity before inclusion.

## Practical takeaway

The paper's quality-over-quantity principle is correct; my disagreement is with how easily teams operationalize it as quantity-after-minimal-filtering. In this domain, policy-risk examples are sparse and non-obvious, so synthetic scaling must be subordinated to failure-bucket saturation. For Tenacious-Bench, this is the difference between a benchmark that catches real outreach risk and one that just grades prose quality.
