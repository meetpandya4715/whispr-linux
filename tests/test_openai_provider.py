from pathlib import Path

import httpx
import pytest

from whisprlinux.config import default_config
from whisprlinux.providers.base import ProviderError
from whisprlinux.providers.openai import OpenAITranscriptionProvider


class Client:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.kwargs = None

    def post(self, *args, **kwargs):
        self.kwargs = kwargs
        return self.response


def test_openai_success(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("whisprlinux.providers.openai.get_openai_key", lambda: "test-key")
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    client = Client(httpx.Response(200, json={"text": " hello "}))
    result = OpenAITranscriptionProvider(client).transcribe(audio, default_config())
    assert result.text == "hello"
    assert client.kwargs["data"]["model"] == "gpt-4o-transcribe"


def test_diarize_model_omits_prompt(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("whisprlinux.providers.openai.get_openai_key", lambda: "test-key")
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    client = Client(httpx.Response(200, json={"text": "hello"}))
    config = default_config().model_copy(update={"model": "gpt-4o-transcribe-diarize", "prompt": "English only"})

    OpenAITranscriptionProvider(client).transcribe(audio, config)

    assert client.kwargs["data"] == {"model": "gpt-4o-transcribe-diarize"}


@pytest.mark.parametrize("status", [401, 429, 400])
def test_openai_errors(monkeypatch, tmp_path: Path, status: int) -> None:
    monkeypatch.setattr("whisprlinux.providers.openai.get_openai_key", lambda: "test-key")
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    with pytest.raises(ProviderError):
        OpenAITranscriptionProvider(Client(httpx.Response(status, json={"error": {"message": "bad"}}))).transcribe(audio, default_config())
