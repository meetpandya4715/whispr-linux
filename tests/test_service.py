from pathlib import Path

from whisprlinux import service
from whisprlinux.service import render_service


def test_render_service_contains_x11_environment() -> None:
    content = render_service("/tmp/whisprlinux", {"DISPLAY": ":1", "XDG_SESSION_TYPE": "x11"})
    assert "Environment=DISPLAY=:1" in content
    assert "Environment=XDG_SESSION_TYPE=x11" in content
    assert "ExecStart=/tmp/whisprlinux daemon --foreground" in content


def test_service_path_is_user_systemd(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert service.service_path() == tmp_path / ".config" / "systemd" / "user" / "whisprlinux.service"


def test_service_logs_falls_back_to_status(monkeypatch) -> None:
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        code = 1 if args[0] == "journalctl" else 0
        return type("Result", (), {"returncode": code})()

    monkeypatch.setattr(service.subprocess, "run", fake_run)
    assert service.service_logs().returncode == 0
    assert calls[0][0] == "journalctl"
    assert calls[1][:3] == ["systemctl", "--user", "status"]
