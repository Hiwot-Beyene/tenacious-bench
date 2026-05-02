# Path memo: ORPO (Hong, Lee, Thorne, EMNLP 2024)

## What I accept

Monolithic preference optimization without an explicit reference model is attractive when we want **one** training phase and a small codebase surface area.

## Why SimPO stays primary for v0.1

ORPO couples preference signal with SFT-like behavior in ways that can **blur** attribution when ablations fail (Act IV). We document ORPO as the **fallback** if SimPO runs show instability on our **short email** completions; the evidence hook is the ablation table, not a paper disagreement for its own sake.
