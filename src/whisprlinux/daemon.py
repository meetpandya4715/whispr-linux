from __future__ import annotations

import threading
from pathlib import Path

from .audio import cleanup_audio, record_until_stopped
from .clipboard import deliver_text
from .config import AppConfig, load_config
from .input_x11 import run_global_listener
from .notify import notify
from .providers.base import ProviderError
from .providers.registry import provider_for_config


class DictationSession:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self.stop_event: threading.Event | None = None
        self.worker: threading.Thread | None = None
        self.audio_path: Path | None = None

    def start_recording(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self._record, daemon=True)
        self.worker.start()

    def stop_recording(self) -> None:
        if self.stop_event:
            self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=self.config.recording_max_seconds + 5)
        self._transcribe_and_deliver()

    def _record(self) -> None:
        if not self.stop_event:
            return
        try:
            self.audio_path = record_until_stopped(self.stop_event, self.config)
        except Exception as exc:
            self.audio_path = None
            if self.config.notify:
                notify("WhisprLinux recording failed", str(exc))

    def _transcribe_and_deliver(self) -> None:
        if not self.audio_path:
            return
        try:
            result = provider_for_config(self.config).transcribe(self.audio_path, self.config)
            if not result.text:
                if self.config.notify:
                    notify("WhisprLinux", "Transcription was empty")
                return
            deliver_text(result.text, self.config)
        except ProviderError as exc:
            if self.config.notify:
                notify("WhisprLinux transcription failed", str(exc))
        except Exception as exc:
            if self.config.notify:
                notify("WhisprLinux output failed", str(exc))
        finally:
            cleanup_audio(self.audio_path, self.config)


def run_daemon(foreground: bool = False) -> None:
    config = load_config()
    session = DictationSession(config)
    if foreground:
        print(f"WhisprLinux listening for {config.hotkey}. Press and hold to dictate.")
    run_global_listener(config.hotkey, session.start_recording, session.stop_recording)
