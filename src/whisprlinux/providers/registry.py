from __future__ import annotations

from pathlib import Path

from whisprlinux.config import AppConfig
from whisprlinux.providers.base import ProviderError, TranscriptionProvider, TranscriptionResult
from whisprlinux.providers.openai import OpenAITranscriptionProvider


class FakeProvider:
    name = "fake"

    def transcribe(self, audio_path: Path, config: AppConfig) -> TranscriptionResult:
        text = config.providers.get("fake", {}).get("text", "fake transcription")
        return TranscriptionResult(text=text, raw={"provider": "fake"})


_PROVIDERS: dict[str, TranscriptionProvider] = {}


def register_provider(name: str, provider: TranscriptionProvider) -> None:
    _PROVIDERS[name] = provider


def provider_names() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider(name: str) -> TranscriptionProvider:
    try:
        return _PROVIDERS[name]
    except KeyError as exc:
        raise ProviderError(f"Unknown transcription provider: {name}") from exc


def provider_for_config(config: AppConfig) -> TranscriptionProvider:
    return get_provider(config.provider)


register_provider("openai", OpenAITranscriptionProvider())
register_provider("fake", FakeProvider())
