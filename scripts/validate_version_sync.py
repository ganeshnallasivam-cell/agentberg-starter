#!/usr/bin/env python3
"""Validate that pyproject.toml version matches kit_manifest.json version.

CI runs this so a kit release that bumps kit_manifest.json but forgets
pyproject.toml is caught before publish.

  validate_version_sync.py          exit 1 on mismatch

Stdlib-only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

manifest_version = json.loads((ROOT / "kit_manifest.json").read_text()).get("version", "")

pyproject_text = (ROOT / "pyproject.toml").read_text()
m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
pyproject_version = m.group(1) if m else ""

if manifest_version != pyproject_version:
    print(f"VERSION MISMATCH: kit_manifest.json={manifest_version!r}  pyproject.toml={pyproject_version!r}")
    print("Both must be bumped together on every release.")
    sys.exit(1)

print(f"OK: versions in sync at {manifest_version}")
