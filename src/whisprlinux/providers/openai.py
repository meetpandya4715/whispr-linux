from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from whisprlinux.config import AppConfig
from whisprlinux.providers.base import ProviderError, TranscriptionResult
from whisprlinux.secrets import get_openai_key


class OpenAITranscriptionProvider:
    name = "openai"
    endpoint = "https://api.openai.com/v1/audio/transcriptions"
    diarize_model = "gpt-4o-transcribe-diarize"

    def __init__(self, client: Any | None = None) -> None:
        self.client = client or httpx

    def transcribe(self, audio_path: Path, config: AppConfig) -> TranscriptionResult:
        api_key = get_openai_key()
        if not api_key:
            raise ProviderError("OpenAI API key missing. Run whisprlinux auth set-openai-key.")
        data: dict[str, str] = {"model": config.model}
        if config.language:
            data["language"] = config.language
        if config.prompt and config.model != self.diarize_model:
            data["prompt"] = config.prompt
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            with audio_path.open("rb") as audio_file:
                files = {"file": (audio_path.name, audio_file, "audio/wav")}
                response = self.client.post(self.endpoint, headers=headers, data=data, files=files, timeout=120)
        except httpx.HTTPError as exc:
            raise ProviderError("OpenAI transcription request failed") from exc
        if response.status_code == 401:
            raise ProviderError("OpenAI authentication failed. Re-check your API key.")
        if response.status_code == 429:
            raise ProviderError("OpenAI rate limit reached. Try again later.")
        if response.status_code >= 400:
            detail = _safe_error(response)
            raise ProviderError(f"OpenAI transcription failed: {detail}")
        payload = response.json()
        text = str(payload.get("text", "")).strip()
        return TranscriptionResult(text=text, raw=payload)


def _safe_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        message = payload.get("error", {}).get("message") or payload.get("message")
        return str(message or f"HTTP {response.status_code}")
    except Exception:
        return f"HTTP {response.status_code}"
