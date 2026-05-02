"""Token-level log-probability of an assistant completion under a causal LM (Path B eval)."""
from __future__ import annotations

from typing import Any, Optional, Tuple

import torch


def completion_neg_log_loss(
    model: Any,
    tokenizer: Any,
    *,
    prompt: str,
    completion: str,
    device: torch.device,
    system: Optional[str] = None,
) -> Tuple[float, int]:
    """
    Mean negative log-likelihood (nats) over completion tokens only (lower is better).
    Uses left-to-right teacher forcing on prompt + completion.
    """
    # Chat template when available (Qwen / Llama instruct)
    if hasattr(tokenizer, "apply_chat_template"):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(
            [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion},
            ]
        )
        full_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
        prefix_msgs = []
        if system:
            prefix_msgs.append({"role": "system", "content": system})
        prefix_msgs.append({"role": "user", "content": prompt})
        prompt_only = tokenizer.apply_chat_template(
            prefix_msgs,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        full_text = f"### User:\n{prompt}\n### Assistant:\n{completion}"
        prompt_only = f"### User:\n{prompt}\n### Assistant:\n"

    full = tokenizer(full_text, return_tensors="pt", add_special_tokens=False)
    prompt_t = tokenizer(prompt_only, return_tensors="pt", add_special_tokens=False)
    input_ids = full["input_ids"].to(device)
    p_ids = prompt_t["input_ids"][0].to(device)
    f_ids = input_ids[0]
    plen = int(p_ids.shape[0])
    if plen > f_ids.shape[0] or not bool(torch.equal(f_ids[:plen], p_ids)):
        raise ValueError("prompt tokenization prefix mismatch; adjust chat template in critic_logprob.py")
    attn = full.get("attention_mask")
    if attn is not None:
        attn = attn.to(device)

    with torch.no_grad():
        out = model(input_ids=input_ids, attention_mask=attn)
        logits = out.logits[:, :-1, :]
        targets = input_ids[:, 1:]
        logp = torch.log_softmax(logits, dim=-1)
        token_logp = logp.gather(-1, targets.unsqueeze(-1)).squeeze(-1)

    # Logits at index plen-1 predicts first completion token at f_ids[plen]
    completion_slice = token_logp[0, plen - 1 :]
    if completion_slice.numel() == 0:
        return 0.0, 0
    nll = float(-completion_slice.mean().item())
    return nll, int(completion_slice.numel())


def prefers_chosen(
    model: Any,
    tokenizer: Any,
    *,
    prompt: str,
    chosen: str,
    rejected: str,
    device: torch.device,
    system: Optional[str] = None,
) -> bool:
    """True if mean NLL(chosen) < mean NLL(rejected)."""
    c, _ = completion_neg_log_loss(
        model, tokenizer, prompt=prompt, completion=chosen, device=device, system=system
    )
    r, _ = completion_neg_log_loss(
        model, tokenizer, prompt=prompt, completion=rejected, device=device, system=system
    )
    return c < r
