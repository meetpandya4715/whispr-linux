from __future__ import annotations

import shutil
import subprocess


def notify(title: str, message: str) -> None:
    if shutil.which("notify-send") is None:
        return
    subprocess.run(["notify-send", title, message], check=False)
