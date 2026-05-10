import pytest

from whisprlinux import secrets


class FakeKeyring:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self.values[(service, username)] = password

    def get_password(self, service: str, username: str) -> str | None:
        return self.values.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        self.values.pop((service, username), None)


def test_openai_key_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeKeyring()
    monkeypatch.setattr(secrets.keyring, "set_password", fake.set_password)
    monkeypatch.setattr(secrets.keyring, "get_password", fake.get_password)
    monkeypatch.setattr(secrets.keyring, "delete_password", fake.delete_password)
    secrets.set_openai_key("test-key")
    assert secrets.get_openai_key() == "test-key"
    secrets.delete_openai_key()
    assert secrets.get_openai_key() is None
