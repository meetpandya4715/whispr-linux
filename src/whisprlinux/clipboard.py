from __future__ import annotations

import subprocess
import time

from .config import AppConfig


class OutputError(RuntimeError):
    pass


def copy_to_clipboard(text: str) -> None:
    proc = subprocess.Popen(
        ["xclip", "-selection", "clipboard"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        _, stderr = proc.communicate(text, timeout=1)
    except subprocess.TimeoutExpired:
        # xclip may remain alive as the X11 clipboard owner after it receives input.
        return
    if proc.returncode != 0:
        raise OutputError((stderr or "xclip failed to write clipboard").strip())


def paste_from_clipboard(delay_ms: int = 120) -> None:
    time.sleep(delay_ms / 1000)
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    with keyboard.pressed(Key.ctrl):
        keyboard.press("v")
        keyboard.release("v")


def deliver_text(text: str, config: AppConfig) -> None:
    if config.output_mode == "stdout":
        print(text)
        return
    copy_to_clipboard(text)
    if config.output_mode == "clipboard_and_paste":
        paste_from_clipboard(config.paste_delay_ms)
