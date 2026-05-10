from pathlib import Path
import threading

import pytest

from whisprlinux.audio import RecordingCancelled, audio_has_voice, ffmpeg_command, parec_command, record_until_stopped
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


def test_recording_waits_for_tail_padding_after_stop(monkeypatch, tmp_path: Path) -> None:
    sleeps = []
    audio = tmp_path / "audio.raw"

    class FakeProcess:
        def terminate(self) -> None:
            audio.write_bytes(b"RIFF")

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr("whisprlinux.audio._require_tools", lambda: None)
    monkeypatch.setattr("whisprlinux.audio.get_default_source", lambda: "mic")
    monkeypatch.setattr("whisprlinux.audio.tempfile.mkdtemp", lambda **kwargs: str(tmp_path))
    monkeypatch.setattr("whisprlinux.audio.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr("whisprlinux.audio.subprocess.run", lambda *args, **kwargs: type("Result", (), {"returncode": 0})())
    monkeypatch.setattr("whisprlinux.audio.time.sleep", sleeps.append)
    monotonic_values = iter([0.0, 0.5, 10.0, 10.1])
    monkeypatch.setattr("whisprlinux.audio.time.monotonic", lambda: next(monotonic_values))

    stop_event = threading.Event()
    stop_event.set()
    config = default_config().model_copy(update={"recording_tail_padding_ms": 450})

    record_until_stopped(stop_event, config)

    assert 0.45 in sleeps


def test_silent_raw_audio_is_cancelled_before_transcription(monkeypatch, tmp_path: Path) -> None:
    audio = tmp_path / "audio.raw"

    class FakeProcess:
        def terminate(self) -> None:
            audio.write_bytes(b"\x00" * 32000)

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr("whisprlinux.audio._require_tools", lambda: None)
    monkeypatch.setattr("whisprlinux.audio.get_default_source", lambda: "mic")
    monkeypatch.setattr("whisprlinux.audio.tempfile.mkdtemp", lambda **kwargs: str(tmp_path))
    monkeypatch.setattr("whisprlinux.audio.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr("whisprlinux.audio.subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not transcode silence")))

    stop_event = threading.Event()
    stop_event.set()
    with pytest.raises(RecordingCancelled, match="No speech detected"):
        record_until_stopped(stop_event, default_config())


def test_audio_has_voice_uses_rms_and_peak_thresholds(tmp_path: Path) -> None:
    audio = tmp_path / "audio.raw"
    audio.write_bytes((0).to_bytes(2, "little", signed=True) * 20)
    assert not audio_has_voice(audio, default_config())

    audio.write_bytes((1000).to_bytes(2, "little", signed=True) * 20)
    assert audio_has_voice(audio, default_config())
