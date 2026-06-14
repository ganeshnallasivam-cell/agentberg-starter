"""
llm.py — Claude ranking layer via Claude Code CLI.

Requires Claude Code CLI installed: claude.ai/code
No API key needed — uses your Claude subscription.

If `claude` CLI is not found, falls back to rule-based ranking automatically.
"""

import character
import json
import os
import shutil
import subprocess


def _find_claude() -> str | None:
    p = shutil.which("claude")
    if p:
        return p
    for d in ("/usr/local/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")):
        fp = os.path.join(d, "claude")
        if os.path.isfile(fp) and os.access(fp, os.X_OK):
            return fp
    return None


def _parse_json(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(raw[start:end])
    return json.loads(raw)


def rank_candidates(
    candidates: list[dict],
    regime: str,
    risk_level: str,
    health_label: str,
    blocked_sectors: list[str],
) -> list[dict]:
    """
    Ask Claude to review candidates. Falls back to rule-based if CLI not found.
    """
    if not candidates:
        return candidates

    claude = _find_claude()
    if not claude:
        print("    [claude] CLI not found — rule-based fallback (install at claude.ai/code)")
        return candidates

    prompt = f"""You are a disciplined trading agent reviewing candidates.

Market context:
- Regime: {regime or "unknown"}
- Risk level: {risk_level or "unknown"}
- Market health: {health_label or "unknown"}
- Blocked sectors (do not trade): {blocked_sectors or "none"}

{character.persona_brief()}

Candidates:
{json.dumps(candidates, indent=2)}

Review each candidate. Honor the operator's character above. Keep at most 3. Skip if sector is blocked,
regime is bear and direction is bullish, or the move is weak (< 1%).
Prefer stronger moves and sectors with tailwinds.

Return a JSON array of candidates to TRADE, priority order.
Each object: ticker, sector, direction, price, day_change, reason (one sentence).
JSON only — no text outside the array."""

    try:
        result = subprocess.run(
            [claude, "-p", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr[:100])
        ranked = _parse_json(result.stdout)
        print(f"    [claude] {len(candidates)} → {len(ranked)} candidate(s)")
        for c in ranked:
            print(f"    [claude] TRADE {c['ticker']}: {c.get('reason', '')}")
        return ranked
    except Exception as e:
        print(f"    [claude] unavailable ({e}) — rule-based fallback")
        return candidates
