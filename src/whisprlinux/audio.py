from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from .config import AppConfig


class AudioError(RuntimeError):
    pass


class RecordingCancelled(AudioError):
    pass


MIN_RECORDING_SECONDS = 0.35


def get_default_source() -> str | None:
    result = subprocess.run(["pactl", "get-default-source"], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def parec_command(raw_path: Path, config: AppConfig) -> list[str]:
    cmd = [
        "parec",
        "--format=s16le",
        f"--rate={config.sample_rate}",
        f"--channels={config.channels}",
    ]
    source = config.audio_source or get_default_source()
    if source:
        cmd.append(f"--device={source}")
    cmd.append(str(raw_path))
    return cmd


def ffmpeg_command(raw_path: Path, wav_path: Path, config: AppConfig) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-ar",
        str(config.sample_rate),
        "-ac",
        str(config.channels),
        "-i",
        str(raw_path),
        str(wav_path),
    ]


def record_for_seconds(seconds: int, out: Path, config: AppConfig) -> Path:
    stop_event = threading.Event()
    timer = threading.Timer(seconds, stop_event.set)
    timer.start()
    try:
        return record_until_stopped(stop_event, config, out_path=out, max_seconds=seconds)
    finally:
        timer.cancel()


def record_until_stopped(
    stop_event: threading.Event,
    config: AppConfig,
    *,
    out_path: Path | None = None,
    max_seconds: int | None = None,
) -> Path:
    _require_tools()
    max_seconds = max_seconds or config.recording_max_seconds
    temp_dir = Path(tempfile.mkdtemp(prefix="whisprlinux-", dir=tempfile.gettempdir()))
    raw_path = temp_dir / "audio.raw"
    wav_path = out_path or (temp_dir / "audio.wav")
    started_at = time.monotonic()
    proc = subprocess.Popen(
        parec_command(raw_path, config),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + max_seconds
    while not stop_event.is_set() and time.monotonic() < deadline:
        time.sleep(0.03)
    elapsed_before_tail = time.monotonic() - started_at
    if stop_event.is_set() and elapsed_before_tail >= MIN_RECORDING_SECONDS:
        time.sleep(config.recording_tail_padding_ms / 1000)
    proc.terminate()
    try:
        _, stderr = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr = proc.communicate()
    elapsed = max(elapsed_before_tail, time.monotonic() - started_at)
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        if elapsed < MIN_RECORDING_SECONDS:
            raise RecordingCancelled("Recording was too short. Hold the hotkey while speaking, then release.")
        detail = (stderr or "").strip()
        if detail:
            raise AudioError(f"No microphone audio was captured: {detail}")
        raise AudioError("No microphone audio was captured")
    result = subprocess.run(ffmpeg_command(raw_path, wav_path, config), capture_output=True, text=True, check=False)
    try:
        raw_path.unlink(missing_ok=True)
    except OSError:
        pass
    if result.returncode != 0:
        raise AudioError("ffmpeg failed to convert captured audio")
    return wav_path


def cleanup_audio(path: Path, config: AppConfig) -> None:
    if config.debug_keep_audio:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _require_tools() -> None:
    missing = [cmd for cmd in ("parec", "ffmpeg") if shutil.which(cmd) is None]
    if missing:
        raise AudioError(f"Missing audio tool(s): {', '.join(missing)}")
