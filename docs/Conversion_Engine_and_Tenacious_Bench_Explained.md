# Conversion Engine vs Tenacious-Bench: Datasets, Traces, and End-to-End Examples

This document explains—in plain language—**what data exists in the Conversion Engine (Week 10)**, **what the agent logs**, and **how Tenacious-Bench (Week 11) uses structured “tasks” to grade outreach behavior**, with **edge cases** and **different company situations**.

---

## Part A — The Conversion Engine: What Are the “Datasets”?

Think of the Conversion Engine as a **factory**: it ingests **reference data** about companies and the market, combines that with **your agent’s actions**, and writes **runtime state** plus **trace logs**.

Below are the **main static datasets** (files on disk) and **dynamic outputs** (what gets produced when the system runs).

### A.1 Static reference datasets (inputs to enrichment)

These are **not** “ML training datasets” in the Week 11 sense. They are **business intelligence tables** the agent uses to ground outreach.

| Dataset / file | Role | Format | Example fields (conceptually) |
|----------------|------|--------|-------------------------------|
| **Crunchbase company sample** | Firmographics: size, industry, URL, region, etc. | JSON array of company objects | `name`, `id`, `website`, `num_employees`, `industries`, `about`, … |
| **Layoffs / workforce-change slice** (`layoffs_fyi.json`) | Signals about layoffs, funding context, dated events for testing | JSON array of rows keyed to `crunchbase_id` / company | `Company`, `Has_Layoffs`, `Date`, `Funds_Raised_USD`, `Source`, … |
| **Seed / style / pricing / transcripts** (under repo paths like `tenacious_sales_data/`) | Brand voice, proof points, discovery scripts | Markdown / PDF / structured copy | Used by composer and narratives—not always “one row per company” |

**Example — Crunchbase row (simplified):** one company might have `name: "Consolety"`, `website: "https://consolety.net"`, `num_employees: "1-10"`, and industries tagged as SEO.

**Example — Layoffs row (two edge cases):**

1. **No layoff event for that snapshot** — `Has_Layoffs: false`, `Date` still set (snapshot date), `Laid_Off_Count` may be null.  
2. **Layoff event present** — `Has_Layoffs: true`, `Date` is event date, counts/percent may be filled.

**Edge case — Funding:** `Funds_Raised_USD` may be a number **or** `null` when unknown. The pipeline is designed so **missing funding is realistic** (not every company has public funding).

**Edge case — Company not in Crunchbase file:** enrichment may fall back to name/domain heuristics or return thinner context; downstream copy should not invent facts.

---

### A.2 Runtime data (what the running system writes)

When you operate the Conversion Engine (API, workers, orchestrator), it persists **state** and **logs**.

| Location (typical) | Purpose | Format |
|--------------------|---------|--------|
| `data/runtime/leads.json` | Lead pipeline state (IDs, stages, attributes) | JSON array (may be empty on fresh install) |
| `data/runtime/workspaces.json` | Workspace / session grouping | JSON |
| `data/runtime/outbound_log.jsonl` | Outbound message log | JSONL |
| `data/runtime/sequence_state.json` | Sequence automation state | JSON |
| `data/runtime/bookings.json` | Calendar / booking records | JSON |

**Layman summary:** static files answer “what’s true in the world (as far as our data knows)?” Runtime files answer “where is this lead in the funnel right now?”

---

### A.3 Two different “trace” logs (easy to confuse)

#### 1) `eval/trace_log.jsonl` — τ² / simulation-style summary

This file stores **one JSON object per line** with fields like `simulation_id`, `task_id`, `domain`, `reward`, `agent_cost`, `duration`. It is useful when you run **benchmark-style simulations** (e.g. retail domain tasks).

**Example line (shape):**

```json
{"agent_cost": 0.017474925, "domain": "retail", "duration": 106.8, "reward": 1.0, "simulation_id": "9f1bceea-...", "task_id": "1", "termination_reason": "user_stop"}
```

**Edge cases:**

- **`reward: 1.0`** vs **`reward: 0.0`** — pass vs fail for that simulated task.  
- **Different `task_id`** — different scenario in the simulator, not necessarily your Tenacious lead id.

#### 2) `eval/agent_trace_log.jsonl` — **your** sales agent pipeline trace

This is the **operational trace** for the Conversion Engine: enrichment, compose, send, reply, book. Each line is one **event** with a **`trace_id`**, **`lead_id`**, **`stage`**, **`decision`**, optional **`tool_calls`**, **`token_cost`**, and **`metadata`**.

**Example — enrichment only (briefs validated, no email yet):**

```json
{
  "trace_id": "add91ecb-273a-4a51-a95f-a139486bdb40",
  "lead_id": "american-anodizing-co",
  "stage": "enrich",
  "decision": "briefs_validated",
  "tool_calls": [
    {"name": "enrichment.crunchbase", "ok": true},
    {"name": "enrichment.job_posts", "ok": true},
    {"name": "enrichment.layoffs", "ok": true},
    {"name": "insights.competitor_gap", "ok": true}
  ],
  "token_cost": 0.0,
  "metadata": {
    "schema_validation": {"hiring_signal_ok": true, "competitor_gap_ok": true},
    "layoffs_signal": {"provider": "apify", "has_layoffs": false}
  }
}
```

**Example — same stage, different company, layoffs from `layoffs_fyi`:**

```json
{
  "trace_id": "0b9a26be-82fe-4e9f-a7d7-a5b5a21471ac",
  "lead_id": "ams-par",
  "stage": "enrich",
  "decision": "briefs_validated",
  "tool_calls": [...],
  "metadata": {
    "layoffs_signal": {
      "provider": "layoffs_fyi",
      "has_layoffs": false,
      "source_url": "https://layoffs.fyi/..."
    }
  }
}
```

**Example — layoffs signal true (sensitive messaging edge case):**

```json
{
  "trace_id": "6f232df2-44c6-442b-8b6c-74e302e72aa9",
  "lead_id": "wizard-labs",
  "stage": "enrich",
  "decision": "briefs_validated",
  "metadata": {
    "layoffs_signal": {
      "provider": "layoffs_fyi",
      "has_layoffs": true,
      "latest_layoff_date": "2026-12-15",
      "source_url": "https://layoffs.fyi/..."
    }
  }
}
```

**Example — enrichment + LLM email composition (token cost non-zero):**

```json
{
  "trace_id": "3ff9c4f5-c9ab-475c-9c7a-a43d422c4c95",
  "lead_id": "contractor-corner",
  "stage": "enrich",
  "decision": "briefs_validated",
  "tool_calls": [
    {"name": "enrichment.crunchbase", "ok": true},
    {"name": "enrichment.job_posts", "ok": true},
    {"name": "enrichment.layoffs", "ok": true},
    {"name": "insights.competitor_gap", "ok": true},
    {"name": "compose.email_llm", "ok": true}
  ],
  "token_cost": 0.00108375,
  "metadata": {
    "llm_usage": {
      "prompt_tokens": 5949,
      "completion_tokens": 319,
      "total_tokens": 6268,
      "calls": 4,
      "cost_usd_openrouter": 0.00108375,
      "model": "openai/gpt-4o-mini"
    },
    "layoffs_signal": {"has_layoffs": true, ...}
  }
}
```

**Example — downstream funnel (send → reply → book) for another company:**

```json
{"trace_id": "de6edd34-0276-41b9-88d8-87a1956d65ef", "lead_id": "alpine-100e", "stage": "send_email", "decision": "sent", "metadata": {"subject": "Context: public hiring snapshot", "to": "..."}}
{"trace_id": "91412980-6b88-4fd5-81d5-b37430c3a531", "lead_id": "alpine-100e", "stage": "reply_handling", "decision": "continue", "metadata": {"intent": "interested", "reply_class": "Curious"}}
{"trace_id": "ac32ab98-d962-4f05-983e-7a7d5ecb555a", "lead_id": "alpine-100e", "stage": "book_discovery", "decision": "booked", "metadata": {"booking_id": 18953155}}
```

**Edge cases to keep in mind:**

| Situation | What you might see | Why it matters |
|-----------|-------------------|----------------|
| **Tool `ok: false`** | enrichment partial failure | Email must not claim facts from failed sources. |
| **`token_cost: 0`** on enrich | no LLM call for that step | Do not assume “no LLM” means “no email”—check other events. |
| **Different `lead_id`** | different company / slug | Same pipeline, different facts and tone constraints. |
| **Layoffs true** | extra moral/brand risk | Messaging must be careful; bench tasks often test calibration. |
| **Weak hiring signal** | few or noisy job posts | Agent should “ask, don’t assert” scale—Tenacious-Bench tests this. |

---

### A.4 End-to-end “story” for one company (Conversion Engine)

1. **Input:** Lead points at a company (domain, Crunchbase id, etc.).  
2. **Enrichment:** System reads Crunchbase + layoffs + job boards + generates **briefs** (hiring signal, competitor gap).  
3. **Compose (optional LLM):** System drafts a personalized email using briefs + Tenacious seed docs.  
4. **Send / reply / book:** Operational stages append more trace lines.

**Output (conceptually):** updated runtime JSON + **append-only** `agent_trace_log.jsonl` lines you can use for debugging, cost accounting, and **Week 11 trace-derived task authoring** (redacted).

---

## Part B — Tenacious-Bench: What Is a “Task”? Inputs and Outputs

Tenacious-Bench is **not** the same as Crunchbase JSON. It is a **benchmark**: each row is a **test case** for *sales behavior* (especially failure modes public benchmarks miss).

### B.1 One task = one exam question

Each task typically includes:

| Field | Meaning |
|-------|---------|
| `task_id` | Stable id for this test. |
| `partition` | `train` / `dev` / `heldout` — for learning vs final evaluation. |
| `source_mode` | How the task was built: trace-derived, programmatic, multi-LLM synthesis, hand-authored adversarial. |
| `failure_dimension` | Which risk bucket it targets (e.g. weak signal, bench over-commit, tone). |
| `input_context` | The **scenario**: prospect, hiring brief, bench summary, prior thread. |
| `candidate_output` | The **email (or text) to grade** — can be “good,” “bad,” or “tricky.” |
| `ground_truth` | **Checkable rules**: required phrases, weak-signal flag, forbid capacity promises, etc. |
| `rubric` + `pass_threshold` | How dimensions are defined and what score counts as pass. |

**Machine output:** Running the scorer returns a **number** (0–100), **pass/fail**, and **per-dimension** notes.

---

### B.2 How you “use” Tenacious-Bench end-to-end (mechanical)

**Input to the evaluator (conceptually):**

1. A **task object** (JSON).  
2. An **agent output string** (usually the email body with `Subject:` line as the first line—see scorer implementation).

**Output:**

- `total_score` (float)  
- `pass` (bool vs `pass_threshold`)  
- `dimensions`: grounding, confidence calibration, tone safety, bench safety, format  

**CLI example (repository root `tenacious-bench/`):**

```bash
python evaluation/scoring_evaluator.py evaluation/tasks_examples/weak_signal_ask_vs_assert.json
```

The script reads `candidate_output` from the JSON file and prints one JSON result line.

---

### B.3 Worked example 1 — Weak public signal (programmatic)

**Scenario:** Public pages show only **two** engineering roles; confidence is **low**; the email must **ask** rather than **assert** “you are scaling hard.”

**Input (abbreviated):** see `evaluation/tasks_examples/weak_signal_ask_vs_assert.json`:

- `ground_truth.weak_signal: true`  
- `required_signals`: mentions like “two open engineering roles” and “hiring”  
- `candidate_output`: polite question about hiring cadence  

**Expected behavior:**

- **Grounding:** mentions required signals.  
- **Confidence calibration:** uses soft / question language, avoids hard assertions.  
- **Tone / bench / format:** no banned phrases, structure ok.

**Typical output:** high score, `pass: true`.

**Edge case — bad candidate:** “You are clearly scaling aggressively with huge hiring” → should **fail** confidence calibration on weak-signal tasks.

---

### B.4 Worked example 2 — Bench / capacity honesty (adversarial guard)

**Scenario:** Prospect asks for a team **next week**; **bench** does **not** support instant commitment.

**Input:** `evaluation/tasks_examples/bench_overcommit_guard.json`:

- `ground_truth.forbid_capacity_commitment: true`  
- `required_signals` include domain skills (e.g. rust/substrate)  

**Good candidate:** verifies scope, avoids promising headcount + start date from cold email.

**Bad candidate:** `evaluation/tasks_examples/bench_overcommit_adversarial_fail.json` — contains “deliver 12,” “guarantee start next week,” condescending / banned wording.

**Output:** fail case scores **low** on `bench_safety` and `tone_safety`, total below threshold.

**Edge case:** model writes fluent, polite text but still **promises capacity** → mechanical scorer should still catch it.

---

### B.5 Worked example 3 — Peer pattern without insulting the prospect (trace-derived style)

**Scenario:** Peers hired MLOps roles; target company has **no** public MLOps posting — email must not imply “you’re behind.”

**Input:** `evaluation/tasks_examples/non_condescending_gap.json`

**Edge case:** Sarcastic or CTO-insulting gap framing → `tone_safety` fails even if “technically” about peers.

---

### B.6 Bulk corpus vs hand-built examples

For scale, the repo may also include **`data/tasks_*.jsonl`** (one task per line). Same schema idea: each line is a full task JSON.

**Edge case — partition leakage:** `train` and `heldout` must not duplicate the same scenario text; Week 11 methodology uses contamination checks for that (n-gram / embedding / time-shift rules).

---

## Part C — How the Two Worlds Connect

| Conversion Engine | Tenacious-Bench |
|-------------------|-----------------|
| **Runs** the agent on **real or synthetic leads** | **Grades** outputs on **Tenacious-specific risks** |
| Produces **`agent_trace_log.jsonl`** events | Can author **trace-derived** tasks from those events (redacted) |
| Uses **Crunchbase / layoffs / jobs** as **world facts** | Uses **brief-like fields** inside `input_context` as **exam premises** (may be synthetic for benchmark) |

**Layman analogy:**

- Conversion Engine = **driver on the road**.  
- Tenacious-Bench = **driving test + rubric** built from the kinds of crashes/near-misses your driver actually had.

---

## Part D — Quick glossary

| Term | Simple meaning |
|------|----------------|
| **JSONL** | One JSON object per line; good for logs and large corpora. |
| **Enrichment** | Fetching/stitching external signals into a structured brief. |
| **Brief** | Short structured summary the email composer conditions on. |
| **Trace** | Time-stamped record of what the system did and decided. |
| **Task (bench)** | A single graded scenario + output + rules. |
| **Evaluator / scorer** | Program that turns (task, output) → numeric score. |
| **Partition** | train/dev/heldout split for honest measurement. |

---

## Where to look in the repos

| Topic | Path |
|-------|------|
| Crunchbase sample | `conversion-engine/data/crunchbase-companies-information.json` |
| Layoffs slice | `conversion-engine/data/layoffs_fyi.json` |
| Agent trace log | `conversion-engine/eval/agent_trace_log.jsonl` |
| τ²-style trace log | `conversion-engine/eval/trace_log.jsonl` |
| Trace emitter | `conversion-engine/agent/agent/structured_logger.py` |
| Bench schema | `tenacious-bench/schema.json` |
| Example tasks | `tenacious-bench/evaluation/tasks_examples/` |
| Scorer | `tenacious-bench/evaluation/scoring_evaluator.py` |
| Materialized task corpus (if present) | `tenacious-bench/data/tasks_*.jsonl` |

---

*Document version: aligned to repository layout as of authoring; file paths may evolve—use this doc as a mental model first, then confirm paths in-tree.*
