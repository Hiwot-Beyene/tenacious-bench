#!/usr/bin/env python3
"""Compatibility shim — use `scripts/build_corpus.py` (canonical corpus builder)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "build_corpus.py"
    # Forward argv: supports e.g. `--out-dir`, `--refresh-seeds`
    raise SystemExit(subprocess.call([sys.executable, str(script), *sys.argv[1:]]))
