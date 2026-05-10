from whisprlinux import clipboard
from whisprlinux.config import default_config


def test_copy_to_clipboard(monkeypatch) -> None:
    calls = []

    class FakeProcess:
        returncode = 0

        def communicate(self, text, timeout):
            calls.append((text, timeout))
            return "", ""

    def fake_popen(args, **kwargs):
        calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr(clipboard.subprocess, "Popen", fake_popen)
    clipboard.copy_to_clipboard("hello")
    assert calls[0][0] == ["xclip", "-selection", "clipboard"]
    assert calls[1] == ("hello", 1)


def test_copy_to_clipboard_allows_xclip_owner_timeout(monkeypatch) -> None:
    class FakeProcess:
        def communicate(self, text, timeout):
            raise clipboard.subprocess.TimeoutExpired("xclip", timeout)

    monkeypatch.setattr(clipboard.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    clipboard.copy_to_clipboard("hello")


def test_stdout_output(capsys) -> None:
    config = default_config().model_copy(update={"output_mode": "stdout"})
    clipboard.deliver_text("hello", config)
    assert "hello" in capsys.readouterr().out


def test_auto_paste_strategy_uses_terminal_shortcut(monkeypatch) -> None:
    pressed = []

    monkeypatch.setattr(clipboard, "active_window_class", lambda: "com.mitchellh.ghostty")
    monkeypatch.setattr(clipboard.time, "sleep", lambda delay: None)
    monkeypatch.setattr(clipboard, "press_hotkey", lambda keys: pressed.append(keys))

    clipboard.paste_from_clipboard(default_config())

    assert pressed == [("ctrl", "shift", "v")]


def test_auto_paste_strategy_uses_standard_shortcut_for_browser(monkeypatch) -> None:
    pressed = []

    monkeypatch.setattr(clipboard, "active_window_class", lambda: "google-chrome")
    monkeypatch.setattr(clipboard.time, "sleep", lambda delay: None)
    monkeypatch.setattr(clipboard, "press_hotkey", lambda keys: pressed.append(keys))

    clipboard.paste_from_clipboard(default_config())

    assert pressed == [("ctrl", "v")]


def test_explicit_terminal_paste_strategy(monkeypatch) -> None:
    pressed = []
    config = default_config().model_copy(update={"paste_strategy": "ctrl_shift_v"})

    monkeypatch.setattr(clipboard, "active_window_class", lambda: "google-chrome")
    monkeypatch.setattr(clipboard.time, "sleep", lambda delay: None)
    monkeypatch.setattr(clipboard, "press_hotkey", lambda keys: pressed.append(keys))

    clipboard.paste_from_clipboard(config)

    assert pressed == [("ctrl", "shift", "v")]


def test_explicit_shift_insert_paste_strategy(monkeypatch) -> None:
    pressed = []
    config = default_config().model_copy(update={"paste_strategy": "shift_insert"})

    monkeypatch.setattr(clipboard, "active_window_class", lambda: "google-chrome")
    monkeypatch.setattr(clipboard.time, "sleep", lambda delay: None)
    monkeypatch.setattr(clipboard, "press_hotkey", lambda keys: pressed.append(keys))

    clipboard.paste_from_clipboard(config)

    assert pressed == [("shift", "insert")]


def test_active_window_class_parses_xprop(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        if args == ["xprop", "-root", "_NET_ACTIVE_WINDOW"]:
            return type("Result", (), {"returncode": 0, "stdout": "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x4200007\n"})()
        if args == ["xprop", "-id", "0x4200007", "WM_CLASS"]:
            return type("Result", (), {"returncode": 0, "stdout": 'WM_CLASS(STRING) = "ghostty", "com.mitchellh.ghostty"\n'})()
        raise AssertionError(args)

    monkeypatch.setattr(clipboard.subprocess, "run", fake_run)

    assert clipboard.active_window_class() == "com.mitchellh.ghostty"
