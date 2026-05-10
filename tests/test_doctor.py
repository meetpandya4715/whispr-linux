from whisprlinux import doctor


def test_doctor_marks_wayland_unsupported(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(doctor, "keyring_available", lambda: True)
    monkeypatch.setattr(doctor, "get_openai_key", lambda: None)
    checks = doctor.run_checks({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME", "XDG_SESSION_TYPE": "wayland", "DISPLAY": ":1"})
    session = next(check for check in checks if check.name == "Session")
    assert not session.ok


def test_doctor_x11(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(doctor, "keyring_available", lambda: True)
    monkeypatch.setattr(doctor, "get_openai_key", lambda: None)
    checks = doctor.run_checks({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME", "XDG_SESSION_TYPE": "x11", "DISPLAY": ":1"})
    assert next(check for check in checks if check.name == "Session").ok
    assert next(check for check in checks if check.name == "Paste backend").ok


def test_doctor_checks_api_connectivity_when_key_exists(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(doctor, "keyring_available", lambda: True)
    monkeypatch.setattr(doctor, "get_openai_key", lambda: "test-key")
    monkeypatch.setattr(doctor, "api_connectivity", lambda key: doctor.Check("OpenAI API", True, "reachable"))
    checks = doctor.run_checks({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME", "XDG_SESSION_TYPE": "x11", "DISPLAY": ":1"})
    assert next(check for check in checks if check.name == "OpenAI API").ok
