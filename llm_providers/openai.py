"""OpenAI adapter — Codex CLI (`codex`). No API key; sign in to `codex` once.

Install: see README.md. If `codex` isn't found, llm.py falls back to rule-based.
Honors LLM_MODEL to override the codex model.

codex streams progress to stderr; --output-last-message captures only the final
answer to a file, which is the cleanest thing to parse.
"""

import os
import shutil
import subprocess
import tempfile

NAME = "openai"
CLI = "codex"


def available() -> bool:
    return shutil.which(CLI) is not None


def run(prompt: str) -> str:
    with tempfile.NamedTemporaryFile("r", suffix=".txt", delete=False) as f:
        out_path = f.name
    cmd = [
        CLI, "exec",
        "--skip-git-repo-check",
        "--sandbox", "read-only",
        "--ask-for-approval", "never",
        "--output-last-message", out_path,
    ]
    model = os.environ.get("LLM_MODEL")
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    try:
        with open(out_path) as f:
            final = f.read()
    except OSError:
        final = ""
    raw = final.strip() or proc.stdout
    if proc.returncode != 0 and not raw.strip():
        err = (proc.stderr or "error").strip().splitlines()
        raise RuntimeError(err[-1] if err else "error")
    return raw
