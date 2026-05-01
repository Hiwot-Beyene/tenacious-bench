# Synthesis: Gebru et al. (Datasheets) + Pushkarna et al. (Data Cards)

## Thesis I accept

Dataset documentation should be a first-class artifact: motivation, composition, collection, cleaning, uses, distribution, and maintenance should be legible without private context. Pushkarna’s layered “telescopic / periscopic / microscopic” view is a practical way to serve both executives and implementers from one repo.

## Design choice I dispute (and what we did instead)

Gebru-style datasheets sometimes treat “uses” as aspirational marketing. For Tenacious-Bench, **uses** and **out-of-scope uses** are written as deployment constraints (no unreviewed live send; no compliance claim from a benchmark pass). That is narrower than a generic “intended for research” paragraph, but it matches the harm model for sales automation.

## Evidence from this repo

- `docs/datasheet.md` mirrors Gebru sections and adds Pushkarna layers with pointers to mechanical checks (`evaluation/scoring_evaluator.py`) and contamination output (`reports/contamination_check.json`).
- The Act II package copies the same datasheet so reviewers see one narrative, not conflicting drafts.

## Takeaway

Layered documentation is not extra prose; it is how you keep benchmark claims accountable when the scorer changes.
