from pathlib import Path

from whisprlinux.audio import ffmpeg_command, parec_command
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
