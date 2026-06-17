"""
setup.py — one-time onboarding. Sets your agent's CHARACTER (persona, risk, goals).

Two ways to run:

  python setup.py               — interactive terminal (answers each question)
  python setup.py --set '...'   — non-interactive (pass JSON or key=value string)

Inside a Claude session, just say:
  "Run my agent setup" — Claude will ask each question conversationally and call
  `python setup.py --set '{"agent_name": ..., ...}'` with your answers.
"""

import json
import os
import sys

import character


def _run_interactive(existing: dict) -> dict:
    answers = dict(existing)
    print("\nAgentberg agent setup — answer each question, or press Enter to keep the current/default.\n")
    for q in character.QUESTIONS:
        current = existing.get(q["id"], q.get("default"))
        prompt = q["q"]
        if q.get("options"):
            prompt += f"  [{'/'.join(q['options'])}]"
        if current not in (None, "", []):
            prompt += f"  (current: {current})"
        try:
            raw = input(prompt + "\n> ").strip()
        except EOFError:
            print("\n[setup] stdin is not a terminal. Use --set or run conversationally via Claude.")
            print("  python setup.py --set '{\"agent_name\": \"MyAgent\", ...}'")
            sys.exit(1)
        if not raw:
            if q.get("required") and not current:
                try:
                    while not raw:
                        raw = input("(required) > ").strip()
                except EOFError:
                    print("\n[setup] Could not read required field in non-interactive mode. Use --set.")
                    sys.exit(1)
                answers[q["id"]] = character.coerce(q, raw)
            else:
                answers[q["id"]] = current
        else:
            answers[q["id"]] = character.coerce(q, raw)
    return answers


def _run_set(arg: str, existing: dict) -> dict:
    """Accept JSON object or key=value pairs.

    key=value mode splits only on commas that precede another key= token, so
    list values like preferred_sectors=Technology,Energy are not truncated.
    """
    import re
    answers = dict(existing)
    arg = arg.strip()
    if arg.startswith("{"):
        updates = json.loads(arg)
    else:
        updates = {}
        for pair in re.split(r",\s*(?=\w+=)", arg):
            if "=" in pair:
                k, v = pair.split("=", 1)
                updates[k.strip()] = v.strip()
    q_map = {q["id"]: q for q in character.QUESTIONS}
    for k, v in updates.items():
        if k in q_map:
            answers[k] = character.coerce(q_map[k], v)
        else:
            answers[k] = v
    return answers


def _print_questions():
    """Print all questions so Claude can ask them conversationally."""
    print("\nAgentberg onboarding questions — ask the human each one, collect answers,")
    print("then call:  python setup.py --set '<JSON with answers>'\n")
    for i, q in enumerate(character.QUESTIONS, 1):
        opts = f"  [{'/'.join(q['options'])}]" if q.get("options") else ""
        dflt = f"  (default: {q['default']})" if q.get("default") not in (None, "", []) else ""
        req = "  *required*" if q.get("required") else ""
        print(f"  {i}. {q['q']}{opts}{dflt}{req}")
    print()


def main():
    args = sys.argv[1:]
    existing = character.load()

    if "--questions" in args:
        _print_questions()
        return

    if "--set" in args:
        idx = args.index("--set")
        if idx + 1 >= len(args):
            print("Usage: python setup.py --set '{\"agent_name\": \"MyAgent\", ...}'")
            sys.exit(1)
        answers = _run_set(args[idx + 1], existing)
    elif not sys.stdin.isatty():
        # Non-interactive: print the questions and tell Claude how to proceed
        print("\n[setup] Not running in a terminal.")
        print("  If you are a Claude agent, run:  python setup.py --questions")
        print("  then ask the human each question and call:  python setup.py --set '<JSON>'")
        print("  If in a terminal, run:  python setup.py\n")
        sys.exit(0)
    else:
        answers = _run_interactive(existing)

    if not answers.get("agent_name"):
        print("[setup] agent_name is required.")
        sys.exit(1)

    character.save(answers)
    print("\n✓ Saved character.json")
    print(f"  {character.summary()}")
    print("  Your agent will operate by this character until you change it.\n")


if __name__ == "__main__":
    main()
