You are selecting between two near-duplicate Tenacious-Bench task candidates.

(Repository implementation: `generation/dedup_pairwise.py` — uses the same priority order below when `judge_scores` are present.)

Select the candidate that is more diagnostic and mechanically gradable.
Priorities:
1) rubric_application_clarity
2) ground_truth_verifiability
3) adversarial distinctness

Return JSON only:
{
  "winner": "A",
  "reason": "one short sentence"
}
