#!/usr/bin/env python3
"""Release notes generator — single source of truth is kit_manifest.json.

The `changelog` array in kit_manifest.json is the canonical, structured record of
what changed in every version. This script renders it into the three version-bearing
surfaces so they can never drift:

  release_notes.py --write              regenerate CHANGELOG.md + sync __init__.py + pyproject.toml
  release_notes.py --check              exit 1 if any surface is out of sync (CI guard)
  release_notes.py --version X.Y.Z      print just that version's notes (for GH Release body)

Stdlib-only on purpose (the kit ships no build deps).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "kit_manifest.json")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")


def _grep_version(path: str, pattern: str) -> str | None:
    import re
    try:
        with open(os.path.join(ROOT, path)) as f:
            m = re.search(pattern, f.read())
            return m.group(1) if m else None
    except OSError:
        return None


def check_version_consistency(manifest: dict) -> list[str]:
    """The four places a version lives must agree, or pull-to-review and the PyPI tag
    guard drift apart (this has bitten us). Returns a list of mismatch messages."""
    want = manifest.get("version", "")
    found = {
        "kit_manifest.json": want,
        "pyproject.toml": _grep_version("pyproject.toml", r'(?m)^version\s*=\s*"([^"]+)"'),
        "agentberg_cli/__init__.py": _grep_version("agentberg_cli/__init__.py", r'__version__\s*=\s*"([^"]+)"'),
        # knowledge.py KIT_VERSION is read dynamically from kit_manifest.json at import time
        # — no literal version string to check here.
    }
    return [f"{f}={v!r} != kit_manifest {want!r}" for f, v in found.items() if v != want]

HEADER = (
    "# Changelog\n\n"
    "All notable changes to the Agentberg kit and CLI.\n\n"
    "This file is generated from `kit_manifest.json` — do not edit by hand.\n"
    "Run `python scripts/release_notes.py --write` after updating the manifest.\n"
)


def _load() -> dict:
    with open(MANIFEST) as f:
        return json.load(f)


def _entry_md(entry: dict) -> str:
    ver = entry.get("version", "?")
    date = entry.get("date", "")
    out = [f"## v{ver} — {date}".rstrip(" —")]
    files = entry.get("files")
    if files:
        out.append("")
        out.append(f"*Files:* {', '.join(files)}")
    out.append("")
    for item in entry.get("added", []):
        out.append(f"- {item}")
    out.append("")
    return "\n".join(out)


def render_changelog(manifest: dict) -> str:
    parts = [HEADER]
    for entry in manifest.get("changelog", []):
        parts.append(_entry_md(entry))
    return "\n".join(parts).rstrip() + "\n"


def notes_for(manifest: dict, version: str) -> str:
    version = version.lstrip("v")
    for entry in manifest.get("changelog", []):
        if entry.get("version") == version:
            # GH Release body: skip the "## vX" heading (the tag is the title already)
            body = ["### What changed", ""]
            for item in entry.get("added", []):
                body.append(f"- {item}")
            files = entry.get("files")
            if files:
                body += ["", f"*Files touched:* {', '.join(files)}"]
            return "\n".join(body) + "\n"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="regenerate CHANGELOG.md")
    g.add_argument("--check", action="store_true", help="fail if CHANGELOG.md is stale")
    g.add_argument("--version", metavar="X.Y.Z", help="print one version's notes")
    args = ap.parse_args()

    manifest = _load()

    if args.version:
        body = notes_for(manifest, args.version)
        if not body:
            print(f"error: version {args.version} not found in {MANIFEST}", file=sys.stderr)
            return 1
        sys.stdout.write(body)
        return 0

    rendered = render_changelog(manifest)

    if args.check:
        current = ""
        if os.path.exists(CHANGELOG):
            with open(CHANGELOG) as f:
                current = f.read()
        problems = []
        if current != rendered:
            problems.append("CHANGELOG.md is out of sync — run: python scripts/release_notes.py --write")
        problems += check_version_consistency(manifest)
        if problems:
            for p in problems:
                print(p, file=sys.stderr)
            return 1
        print(f"CHANGELOG.md in sync; version {manifest.get('version')} consistent across all files.")
        return 0

    with open(CHANGELOG, "w") as f:
        f.write(rendered)
    print(f"Wrote {CHANGELOG}")

    # Sync all version-bearing surfaces so --write is the single atomic operation.
    import re
    version = manifest.get("version", "")

    # agentberg_cli/__init__.py
    init_path = os.path.join(ROOT, "agentberg_cli/__init__.py")
    with open(init_path) as f:
        init_text = f.read()
    new_init = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', init_text)
    if new_init != init_text:
        with open(init_path, "w") as f:
            f.write(new_init)
        print(f"Synced agentberg_cli/__init__.py to {version}")

    # pyproject.toml
    pyproject_path = os.path.join(ROOT, "pyproject.toml")
    with open(pyproject_path) as f:
        pyproject_text = f.read()
    new_pyproject = re.sub(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', pyproject_text)
    if new_pyproject != pyproject_text:
        with open(pyproject_path, "w") as f:
            f.write(new_pyproject)
        print(f"Synced pyproject.toml to {version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
