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
