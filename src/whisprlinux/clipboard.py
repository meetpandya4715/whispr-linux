from __future__ import annotations

import subprocess
import time
from collections.abc import Sequence

from .config import AppConfig


class OutputError(RuntimeError):
    pass


TERMINAL_WINDOW_CLASSES = {
    "alacritty",
    "com.mitchellh.ghostty",
    "gnome-terminal",
    "gnome-terminal-server",
    "ghostty",
    "kgx",
    "kitty",
    "konsole",
    "org.gnome.console",
    "org.gnome.terminal",
    "terminator",
    "tilix",
    "wezterm",
    "xterm",
}


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


def paste_from_clipboard(config: AppConfig) -> None:
    time.sleep(config.paste_delay_ms / 1000)
    press_hotkey(paste_hotkey(config))


def paste_hotkey(config: AppConfig) -> tuple[str, ...]:
    if config.paste_strategy == "shift_insert":
        return ("shift", "insert")
    if config.paste_strategy == "ctrl_shift_v":
        return ("ctrl", "shift", "v")
    if config.paste_strategy == "ctrl_v":
        return ("ctrl", "v")
    window_class = active_window_class()
    if window_class in TERMINAL_WINDOW_CLASSES:
        return ("ctrl", "shift", "v")
    return ("ctrl", "v")


def active_window_class() -> str | None:
    active = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, check=False)
    if active.returncode != 0:
        return None
    window_id = active.stdout.rsplit(" ", 1)[-1].strip()
    if not window_id or window_id == "0x0":
        return None
    window = subprocess.run(["xprop", "-id", window_id, "WM_CLASS"], capture_output=True, text=True, check=False)
    if window.returncode != 0:
        return None
    classes = [part.strip().strip('"').lower() for part in window.stdout.split(",")]
    return classes[-1] if classes else None


def press_hotkey(keys: Sequence[str]) -> None:
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    modifiers = {"ctrl": Key.ctrl, "shift": Key.shift}
    special_keys = {"insert": Key.insert}
    held = [modifiers[key] for key in keys[:-1]]
    key = special_keys.get(keys[-1], keys[-1])
    for modifier in held:
        keyboard.press(modifier)
    try:
        keyboard.press(key)
        keyboard.release(key)
    finally:
        for modifier in reversed(held):
            keyboard.release(modifier)


def deliver_text(text: str, config: AppConfig) -> None:
    if config.output_mode == "stdout":
        print(text)
        return
    copy_to_clipboard(text)
    if config.output_mode == "clipboard_and_paste":
        paste_from_clipboard(config)
