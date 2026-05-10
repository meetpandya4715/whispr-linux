from __future__ import annotations

import getpass
import os

import keyring
from keyring.errors import KeyringError, NoKeyringError


SERVICE_NAME = "whisprlinux"
OPENAI_USERNAME = "openai_api_key"


class SecretError(RuntimeError):
    pass


def set_openai_key(key: str | None = None) -> None:
    key = key if key is not None else getpass.getpass("OpenAI API key: ")
    if not key.strip():
        raise SecretError("No key provided")
    try:
        keyring.set_password(SERVICE_NAME, OPENAI_USERNAME, key.strip())
    except (KeyringError, NoKeyringError) as exc:
        raise SecretError(_fallback_message()) from exc


def get_openai_key() -> str | None:
    try:
        stored = keyring.get_password(SERVICE_NAME, OPENAI_USERNAME)
    except (KeyringError, NoKeyringError):
        stored = None
    return stored or os.environ.get("OPENAI_API_KEY")


def has_openai_key() -> bool:
    return bool(get_openai_key())


def delete_openai_key() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, OPENAI_USERNAME)
    except (KeyringError, NoKeyringError) as exc:
        raise SecretError(_fallback_message()) from exc
    except Exception:
        pass


def keyring_available() -> bool:
    try:
        keyring.get_keyring()
        return True
    except (KeyringError, NoKeyringError):
        return False


def _fallback_message() -> str:
    return (
        "No usable desktop keyring is available. For this shell only, run: "
        "export OPENAI_API_KEY='your-api-key'"
    )
