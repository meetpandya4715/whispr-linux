from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


ALIASES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "super": "super",
    "cmd": "super",
    "win": "super",
    "alt": "alt",
    "shift": "shift",
    "space": "space",
}


def parse_hotkey(value: str) -> frozenset[str]:
    parts = [part.strip().lower() for part in value.split("+") if part.strip()]
    if not parts:
        raise ValueError("hotkey must contain at least one key")
    return frozenset(ALIASES.get(part, part) for part in parts)


def normalize_key(key: object) -> str:
    name = getattr(key, "name", None)
    if name:
        normalized = name.lower()
    else:
        char = getattr(key, "char", None)
        normalized = str(char or key).lower().strip("'")
    if normalized.startswith("ctrl"):
        return "ctrl"
    if normalized in {"cmd", "cmd_l", "cmd_r", "super_l", "super_r"}:
        return "super"
    if normalized.startswith("alt"):
        return "alt"
    if normalized.startswith("shift"):
        return "shift"
    return ALIASES.get(normalized, normalized)


@dataclass
class HotkeyStateMachine:
    chord: frozenset[str]
    on_start: Callable[[], None]
    on_stop: Callable[[], None]
    pressed: set[str] = field(default_factory=set)
    recording: bool = False

    def press(self, key: str) -> None:
        self.pressed.add(key)
        if not self.recording and self.chord.issubset(self.pressed):
            self.recording = True
            self.on_start()

    def release(self, key: str) -> None:
        was_in_chord = key in self.chord
        self.pressed.discard(key)
        if self.recording and was_in_chord:
            self.recording = False
            self.on_stop()


def run_global_listener(hotkey: str, on_start: Callable[[], None], on_stop: Callable[[], None]) -> None:
    from pynput import keyboard

    machine = HotkeyStateMachine(parse_hotkey(hotkey), on_start, on_stop)

    def handle_press(key: object) -> None:
        machine.press(normalize_key(key))

    def handle_release(key: object) -> None:
        machine.release(normalize_key(key))

    with keyboard.Listener(on_press=handle_press, on_release=handle_release) as listener:
        listener.join()
