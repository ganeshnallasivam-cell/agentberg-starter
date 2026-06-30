#!/usr/bin/env python3
"""
setup_autostart.py — Register this agent as a macOS launchd service.

Installs ~/Library/LaunchAgents/ai.agentberg.<agent_id>.plist and loads it
so the scheduler starts automatically on login and restarts if it crashes.

Run once from inside your agent folder:
    python3 setup_autostart.py

To uninstall:
    python3 setup_autostart.py --uninstall
"""

import os
import re
import subprocess
import sys
from pathlib import Path

LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"


def _read_agent_id(folder: Path) -> str:
    # Try .agent_id file first (written by register on first run)
    aid_file = folder / ".agent_id"
    if aid_file.exists():
        v = aid_file.read_text().strip()
        if v:
            return v
    # Fall back to .env AGENT_ID
    env_file = folder / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            m = re.match(r"^\s*AGENT_ID\s*=\s*['\"]?([^'\"#\s]+)", line)
            if m:
                return m.group(1)
    return folder.name.lower().replace(" ", "-")


def _plist_label(agent_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9.\-]", "-", agent_id).lower()
    return f"ai.agentberg.{safe}"


def _plist_path(label: str) -> Path:
    return LAUNCH_AGENTS / f"{label}.plist"


def _python_path() -> str:
    venv = Path(sys.executable).parent.parent
    if (venv / "bin" / "python3").exists():
        return str(venv / "bin" / "python3")
    return sys.executable


def _generate_plist(label: str, folder: Path, python: str) -> str:
    run_sh = folder / "run.sh"
    logs = folder / "logs"
    stdout = str(logs / "autostart.log")
    stderr = str(logs / "autostart-err.log")

    if run_sh.exists():
        prog_args = f"""
    <array>
        <string>/bin/bash</string>
        <string>{run_sh}</string>
    </array>"""
    else:
        prog_args = f"""
    <array>
        <string>{python}</string>
        <string>{folder / "scheduler.py"}</string>
    </array>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>{prog_args}

    <key>WorkingDirectory</key>
    <string>{folder}</string>

    <key>KeepAlive</key>
    <true/>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{stdout}</string>

    <key>StandardErrorPath</key>
    <string>{stderr}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""


def install(folder: Path) -> None:
    if sys.platform != "darwin":
        sys.exit("ERROR: setup_autostart.py is macOS only (launchd). Use systemd on Linux.")

    agent_id = _read_agent_id(folder)
    label = _plist_label(agent_id)
    plist_path = _plist_path(label)
    python = _python_path()

    (folder / "logs").mkdir(exist_ok=True)
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)

    # Unload existing if present
    if plist_path.exists():
        subprocess.run(["launchctl", "unload", str(plist_path)],
                       capture_output=True)

    plist_content = _generate_plist(label, folder, python)
    plist_path.write_text(plist_content)
    print(f"  Wrote {plist_path}")

    result = subprocess.run(["launchctl", "load", str(plist_path)],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR loading plist: {result.stderr.strip()}")
        sys.exit(1)

    print(f"  Loaded service: {label}")
    print(f"  Agent '{agent_id}' will now start automatically on login.")
    print(f"  Logs → {folder}/logs/autostart.log")
    print()
    print(f"  To stop:      launchctl unload {plist_path}")
    print(f"  To uninstall: python3 setup_autostart.py --uninstall")


def uninstall(folder: Path) -> None:
    agent_id = _read_agent_id(folder)
    label = _plist_label(agent_id)
    plist_path = _plist_path(label)

    if not plist_path.exists():
        print(f"  No plist found at {plist_path} — nothing to uninstall.")
        return

    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    plist_path.unlink()
    print(f"  Unloaded and removed {plist_path}")


def main() -> None:
    folder = Path.cwd()
    if not (folder / "scheduler.py").exists():
        sys.exit("ERROR: Run this from inside your agent folder (scheduler.py not found).")

    if "--uninstall" in sys.argv:
        uninstall(folder)
    else:
        install(folder)


if __name__ == "__main__":
    main()
