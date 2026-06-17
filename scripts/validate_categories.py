#!/usr/bin/env python3
"""Validate the upgrade-category tags in kit_manifest.json.

Every changelog entry must carry a `category` of 0, A, or B (see UPGRADING.md).
Category 0 means "advisory context, empty-safe, override-able — safe to auto-apply".
To keep that promise machine-checkable, a Category 0 entry may NOT touch files that
are inherently execution-logic, identity, or strategy plumbing: an advisory change
lives in the prompt/client/wiring/docs, never in the risk engine or the scheduler.

CI runs this so a mis-tagged release can't ship code that `agentberg upgrade --auto`
would then apply unattended.

  validate_categories.py          exit 1 on any violation

Stdlib-only (the kit ships no build deps).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "kit_manifest.json")

VALID = {"0", "A", "B"}

# Files a Category 0 (advisory) entry must never touch. These are execution logic,
# identity, or strategy plumbing — changes here can alter how the agent decides or
# trades, which is exactly what must not auto-apply.
CAT0_DENY = {
    "risk.py", "structures.py", "config.py", "scheduler.py",
    "alpaca.py", "identity.py", "character.py", "setup.py", "run.sh",
}


def main() -> int:
    with open(MANIFEST) as f:
        manifest = json.load(f)

    errors: list[str] = []
    for entry in manifest.get("changelog", []):
        ver = entry.get("version", "?")
        cat = str(entry.get("category", ""))
        if cat not in VALID:
            errors.append(f"v{ver}: category {entry.get('category')!r} not in {sorted(VALID)}")
            continue
        if cat == "0":
            bad = [f for f in entry.get("files", []) if f.split("/")[0] in CAT0_DENY]
            if bad:
                errors.append(
                    f"v{ver}: Category 0 but touches non-advisory file(s): {bad}. "
                    f"Split the advisory change into its own 0 entry, or tag this A/B."
                )

    if errors:
        print("Category validation FAILED:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"Category validation OK — {len(manifest.get('changelog', []))} entries tagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
