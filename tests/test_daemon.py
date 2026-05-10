from pathlib import Path

from whisprlinux.config import default_config
from whisprlinux.daemon import DictationSession


def test_daemon_delivers_text(monkeypatch, tmp_path: Path) -> None:
    delivered = []
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    session = DictationSession(default_config().model_copy(update={"provider": "fake"}))
    session.audio_path = audio
    monkeypatch.setattr("whisprlinux.daemon.deliver_text", lambda text, config: delivered.append(text))
    session._transcribe_and_deliver()
    assert delivered == ["fake transcription"]
