from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass

from .config import load_config
from .secrets import has_openai_key, keyring_available


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_checks(env: dict[str, str] | None = None) -> list[Check]:
    env = env or os.environ
    checks = [
        Check("Python", platform.python_version_tuple() >= ("3", "13"), platform.python_version()),
    ]
    session = env.get("XDG_SESSION_TYPE", "")
    checks.append(Check("Session", session == "x11", f"{session or 'unknown'} {'ok' if session == 'x11' else 'unsupported'}"))
    display = env.get("DISPLAY", "")
    checks.append(Check("Display", bool(display), display or "missing DISPLAY"))
    checks.extend(
        Check(label, shutil.which(cmd) is not None, shutil.which(cmd) or f"missing; install {cmd}")
        for label, cmd in [
            ("PulseAudio", "pactl"),
            ("Recorder", "parec"),
            ("Transcoder", "ffmpeg"),
            ("Clipboard", "xclip"),
        ]
    )
    checks.append(Check("Keyring", keyring_available(), "available" if keyring_available() else "unavailable; use OPENAI_API_KEY for this shell"))
    try:
        load_config()
        checks.append(Check("Config", True, "readable"))
    except Exception as exc:
        checks.append(Check("Config", False, str(exc)))
    checks.append(Check("API key", has_openai_key(), "available" if has_openai_key() else "missing; run whisprlinux auth set-openai-key"))
    return checks


def api_connectivity(api_key: str, client: object | None = None) -> Check:
    import httpx

    client = client or httpx
    try:
        response = client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if response.status_code == 200:
            return Check("OpenAI API", True, "reachable")
        if response.status_code == 401:
            return Check("OpenAI API", False, "authentication failed")
        return Check("OpenAI API", False, f"HTTP {response.status_code}")
    except Exception as exc:
        return Check("OpenAI API", False, str(exc))


def default_source() -> str | None:
    try:
        result = subprocess.run(["pactl", "get-default-source"], check=True, capture_output=True, text=True)
        return result.stdout.strip() or None
    except Exception:
        return None
