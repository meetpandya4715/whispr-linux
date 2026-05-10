from whisprlinux.input_x11 import HotkeyStateMachine


def test_release_any_chord_key_stops() -> None:
    events = []
    machine = HotkeyStateMachine(frozenset({"shift", "f9"}), lambda: events.append("start"), lambda: events.append("stop"))
    machine.press("shift")
    machine.press("f9")
    machine.release("shift")
    assert events == ["start", "stop"]
