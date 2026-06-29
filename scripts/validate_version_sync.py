#!/usr/bin/env python3
"""Validate that all version markers agree with kit_manifest.json.

Checks three independent files so a bump that forgets any one of them is
caught before CI or publish runs.

  validate_version_sync.py          exit 1 on any mismatch

Stdlib-only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

manifest_version = json.loads((ROOT / "kit_manifest.json").read_text()).get("version", "")

def _extract(path: Path, pattern: str) -> str:
    m = re.search(pattern, path.read_text(), re.MULTILINE)
    return m.group(1) if m else ""

checks = {
    "pyproject.toml":           _extract(ROOT / "pyproject.toml",          r'^version\s*=\s*"([^"]+)"'),
    "agentberg_cli/__init__.py": _extract(ROOT / "agentberg_cli/__init__.py", r'__version__\s*=\s*"([^"]+)"'),
}

mismatches = [
    f"  {name}: {ver!r} != kit_manifest {manifest_version!r}"
    for name, ver in checks.items()
    if ver != manifest_version
]

if mismatches:
    print(f"VERSION MISMATCH — kit_manifest.json={manifest_version!r}")
    for line in mismatches:
        print(line)
    print("All three must be bumped together on every release.")
    sys.exit(1)

print(f"OK: versions in sync at {manifest_version}")
