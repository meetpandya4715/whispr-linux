from pathlib import Path

from whisprlinux.config import default_config
from whisprlinux.daemon import DictationSession


def test_daemon_delivers_text(monkeypatch, tmp_path: Path) -> None:
    delivered = []
    statuses = []
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    session = DictationSession(default_config().model_copy(update={"provider": "fake"}), status=statuses.append)
    session.audio_path = audio
    monkeypatch.setattr("whisprlinux.daemon.deliver_text", lambda text, config: delivered.append(text))
    session._transcribe_and_deliver()
    assert delivered == ["fake transcription"]
    assert statuses == ["transcribing", "text-delivered"]


def test_daemon_treats_short_recording_as_cancelled(monkeypatch) -> None:
    statuses = []
    session = DictationSession(default_config(), status=statuses.append)
    monkeypatch.setattr(
        "whisprlinux.daemon.record_until_stopped",
        lambda *args, **kwargs: (_ for _ in ()).throw(__import__("whisprlinux.audio").audio.RecordingCancelled("too short")),
    )
    session.stop_event = __import__("threading").Event()
    session._record()
    assert session.audio_path is None
    assert statuses == ["recording-cancelled: too short"]
