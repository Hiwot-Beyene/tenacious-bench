"""Reduce Hugging Face Hub / HTTP client noise on the root logger (training-grade defaults)."""
from __future__ import annotations

import logging

# Only dial back low-level HTTP libraries. Keep `huggingface_hub` at default so Hub
# emits normal download/progress messages; keep `filelock` at default so lock waits
# are debuggable if a library logs them.
_HUB_HTTP_LOGGERS = (
    "httpx",
    "httpcore",
    "httpcore.connection",
    "httpcore.http11",
    "urllib3",
    "urllib3.connectionpool",
    "datasets",
)


def silence_hub_http_noise() -> None:
    """Stop per-request INFO lines from polluting training_run.log when root is INFO."""
    for name in _HUB_HTTP_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
