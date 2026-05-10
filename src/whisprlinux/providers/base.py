from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from whisprlinux.config import AppConfig


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    raw: dict = field(default_factory=dict)


class TranscriptionProvider(Protocol):
    name: str

    def transcribe(self, audio_path: Path, config: AppConfig) -> TranscriptionResult:
        ...


class ProviderError(RuntimeError):
    pass
