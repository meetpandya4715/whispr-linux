from __future__ import annotations

import subprocess
import time

from .config import AppConfig


class OutputError(RuntimeError):
    pass


def copy_to_clipboard(text: str) -> None:
    result = subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise OutputError("xclip failed to write clipboard")


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
