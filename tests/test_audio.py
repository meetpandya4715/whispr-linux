from pathlib import Path
import threading

import pytest

from whisprlinux.audio import RecordingCancelled, ffmpeg_command, parec_command, record_until_stopped
from whisprlinux.config import default_config


def test_parec_command(monkeypatch) -> None:
    monkeypatch.setattr("whisprlinux.audio.get_default_source", lambda: "mic")
    cmd = parec_command(Path("/tmp/a.raw"), default_config())
    assert "--format=s16le" in cmd
    assert "--device=mic" in cmd


def test_ffmpeg_command() -> None:
    cmd = ffmpeg_command(Path("/tmp/a.raw"), Path("/tmp/a.wav"), default_config())
    assert cmd[:3] == ["ffmpeg", "-y", "-f"]
    assert "/tmp/a.wav" in cmd


def test_short_empty_recording_is_cancelled(monkeypatch, tmp_path: Path) -> None:
    class FakeProcess:
        def terminate(self) -> None:
            pass

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr("whisprlinux.audio._require_tools", lambda: None)
    monkeypatch.setattr("whisprlinux.audio.get_default_source", lambda: "mic")
    monkeypatch.setattr("whisprlinux.audio.tempfile.mkdtemp", lambda **kwargs: str(tmp_path))
    monkeypatch.setattr("whisprlinux.audio.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    stop_event = threading.Event()
    stop_event.set()
    with pytest.raises(RecordingCancelled):
        record_until_stopped(stop_event, default_config())
