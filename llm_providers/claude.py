"""Claude adapter — Claude Code CLI. No API key; uses your Claude subscription.

Install: claude.ai/code. If `claude` isn't found, llm.py falls back to rule-based.
"""

import os
import shutil
import subprocess

NAME = "claude"


def _find() -> str | None:
    p = shutil.which("claude")
    if p:
        return p
    for d in ("/usr/local/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")):
        fp = os.path.join(d, "claude")
        if os.path.isfile(fp) and os.access(fp, os.X_OK):
            return fp
    return None


def available() -> bool:
    return _find() is not None


def run(prompt: str) -> str:
    proc = subprocess.run(
        [_find(), "-p", "-"], input=prompt,
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "error").strip()[:120])
    return proc.stdout
