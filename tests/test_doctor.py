from whisprlinux import doctor


def test_doctor_marks_wayland_unsupported(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(doctor, "keyring_available", lambda: True)
    monkeypatch.setattr(doctor, "has_openai_key", lambda: True)
    checks = doctor.run_checks({"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":1"})
    session = next(check for check in checks if check.name == "Session")
    assert not session.ok


def test_doctor_x11(monkeypatch) -> None:
    monkeypatch.setattr(doctor.shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    monkeypatch.setattr(doctor, "keyring_available", lambda: True)
    monkeypatch.setattr(doctor, "has_openai_key", lambda: True)
    checks = doctor.run_checks({"XDG_SESSION_TYPE": "x11", "DISPLAY": ":1"})
    assert next(check for check in checks if check.name == "Session").ok
