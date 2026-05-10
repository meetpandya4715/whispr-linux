from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SERVICE_NAME = "whisprlinux.service"


def service_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / SERVICE_NAME


def command_path() -> str:
    venv_command = Path(sys.prefix) / "bin" / "whisprlinux"
    if venv_command.exists():
        return str(venv_command)
    return shutil.which("whisprlinux") or "uv run whisprlinux"


def render_service(exec_start: str | None = None, env: dict[str, str] | None = None) -> str:
    env = env or os.environ
    display = env.get("DISPLAY", ":1")
    session = env.get("XDG_SESSION_TYPE", "x11")
    exec_start = exec_start or command_path()
    if exec_start.startswith("uv "):
        exec_start = f"/usr/bin/env {exec_start} daemon --foreground"
    else:
        exec_start = f"{exec_start} daemon --foreground"
    return f"""[Unit]
Description=WhisprLinux hold-to-dictate service
After=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY={display}
Environment=XDG_SESSION_TYPE={session}
ExecStart={exec_start}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""


def install_service() -> Path:
    path = service_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_service(), encoding="utf-8")
    _systemctl("daemon-reload")
    return path


def uninstall_service() -> None:
    service_path().unlink(missing_ok=True)
    _systemctl("daemon-reload")


def service_action(action: str) -> subprocess.CompletedProcess[str]:
    args = [action]
    if action not in {"daemon-reload"}:
        args.append(SERVICE_NAME)
    return _systemctl(*args)


def service_logs() -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["journalctl", "--user", "-u", SERVICE_NAME, "-n", "80", "--no-pager", "-q"],
        text=True,
        check=False,
        capture_output=True,
    )
    if result.returncode == 0:
        if result.stdout:
            print(result.stdout, end="")
        return result
    args = ["systemctl", "--user", "status", SERVICE_NAME, "--no-pager"]
    subprocess.run(args, text=True, check=False)
    return subprocess.CompletedProcess(args, 0)


def _systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["systemctl", "--user", *args], text=True, check=False)
