# Path memo: DPO (Rafailov et al., NeurIPS 2023)

## What I accept

Preference optimization is the right outer loop for a **critic** when we can pair acceptable vs unacceptable completions under the same context. The Bradley–Terry reduction is clear and implementable in TRL/Unsloth.

## Where I hesitate for Tenacious-Bench v0.1

DPO’s **implicit reward** is tied to a **reference policy** π_ref. Our Week 10 stack already mixes multiple generators; freezing a single π_ref that does not match production logits can **distort** what “margin” means for sales-safety violations that are rare in the reference tail.

**Evidence-based choice:** we default training narrative to **SimPO** for the first run (see `docs/methodology_rationale.md`) and keep DPO as the conceptual baseline and ablation hook.
