from whisprlinux.input_x11 import HotkeyStateMachine, parse_hotkey


def test_parse_hotkey_aliases() -> None:
    assert parse_hotkey("control+win") == frozenset({"ctrl", "super"})


def test_hotkey_state_machine_ignores_repeats() -> None:
    events = []
    machine = HotkeyStateMachine(frozenset({"ctrl", "super"}), lambda: events.append("start"), lambda: events.append("stop"))
    machine.press("ctrl")
    machine.press("super")
    machine.press("super")
    machine.release("super")
    assert events == ["start", "stop"]
