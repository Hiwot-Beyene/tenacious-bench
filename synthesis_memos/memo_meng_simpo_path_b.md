# Path memo: SimPO (Meng, Xia, Chen, NeurIPS 2024)

## What I accept

Reference-free preference optimization reduces operational friction: no paired reference forward pass at scale, which matters under the Week 11 **$10** compute envelope and Colab T4 defaults.

## A design tension

SimPO’s length normalization targets generic chat skew; **email drafts** have hard external constraints (subject length, banned lexicon, “no bench externally”). Length is the wrong proxy for some Tenacious failures.

**Our mitigation:** training pairs are **filtered by `score_task`** on both chosen and rejected, and prompts exclude the draft so the model learns **policy** not memorized subject lines from the prompt.
