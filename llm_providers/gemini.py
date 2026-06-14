"""Gemini adapter — Antigravity CLI (`agy`). No API key; sign in to `agy` once.

Install: see README.md. If `agy` isn't found, llm.py falls back to rule-based.
Honors LLM_MODEL to override the agy model (see `agy models`).
"""

import os
import shutil
import subprocess

NAME = "gemini"
CLI = "agy"


def available() -> bool:
    return shutil.which(CLI) is not None


def run(prompt: str) -> str:
    cmd = [CLI, "-p", prompt, "--print-timeout", "120s"]
    model = os.environ.get("LLM_MODEL")
    if model:
        cmd += ["--model", model]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "error").strip().splitlines()
        raise RuntimeError(err[-1] if err else "error")
    return proc.stdout
