"""Optional OpenRouter client for pointwise judging (same schema as `pointwise_judge.py`).

Configuration (distinct from bulk synthesis calls):
- `OPENROUTER_API_KEY` — required for live calls.
- `OPENROUTER_JUDGE_MODEL` — overrides the model id (defaults to the dev-tier judge paired in
  `model_routing.py` for the task's bulk generator).

The committed v0.1 pipeline uses `pointwise_judge.mechanical_pointwise_scores` so CI stays
deterministic; enable this module when you want API-backed judge scores on a sample.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def score_task_pointwise_api(
    *,
    judge_model: str,
    pointwise_prompt: str,
    task_json: str,
    timeout_s: float = 120.0,
) -> Optional[Dict[str, Any]]:
    """
    POST a chat completion; expect JSON with input_coherence, ground_truth_verifiability,
    rubric_application_clarity (1–5). Returns None if no API key or HTTP error.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    body = {
        "model": judge_model,
        "messages": [
            {"role": "system", "content": pointwise_prompt},
            {"role": "user", "content": task_json[:120_000]},
        ],
        "temperature": 0,
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
