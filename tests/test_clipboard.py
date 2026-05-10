from whisprlinux import clipboard
from whisprlinux.config import default_config


def test_copy_to_clipboard(monkeypatch) -> None:
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(clipboard.subprocess, "run", fake_run)
    clipboard.copy_to_clipboard("hello")
    assert calls[0][0] == ["xclip", "-selection", "clipboard"]
    assert calls[0][1]["input"] == "hello"


def test_stdout_output(capsys) -> None:
    config = default_config().model_copy(update={"output_mode": "stdout"})
    clipboard.deliver_text("hello", config)
    assert "hello" in capsys.readouterr().out
