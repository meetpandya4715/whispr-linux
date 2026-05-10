# Manual Verification Checklist

Use this checklist after storing a real OpenAI API key with `uv run whisprlinux auth set-openai-key`.

## Environment

- [ ] `uv run pytest -v` passes.
- [ ] `uv run whisprlinux doctor` reports Python, Desktop, Session, Display, PulseAudio, Recorder, Transcoder, Clipboard, Paste backend, Keyring, Config, API key, and OpenAI API as ok.
- [ ] `uv run whisprlinux config show` contains the expected `model`, `hotkey`, and `output_mode`.

## Live Microphone And Transcription

- [ ] `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav` creates a playable WAV.
- [ ] `uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav` returns the spoken text.
- [ ] No API key appears in terminal output, config files, git diff, or service logs.

## Clipboard And Paste

- [ ] `uv run whisprlinux config set output_mode clipboard` copies transcribed text without pasting.
- [ ] `uv run whisprlinux paste-test "hello from whisprlinux"` places text in the clipboard.
- [ ] `uv run whisprlinux config set output_mode clipboard_and_paste` pastes into a text editor after clipboard-only mode is confirmed.

## Hold-To-Talk Daemon

- [ ] `uv run whisprlinux daemon --foreground` starts and prints the configured hotkey.
- [ ] Holding the configured chord starts recording.
- [ ] Releasing any key in the chord stops recording.
- [ ] The resulting transcription appears according to `output_mode`.
- [ ] API errors, empty speech, or paste failures do not replace the clipboard with bad text.

## User Service

- [ ] `uv run whisprlinux service install` writes `~/.config/systemd/user/whisprlinux.service`.
- [ ] `uv run whisprlinux service restart` starts the daemon.
- [ ] `uv run whisprlinux service status` shows the service running.
- [ ] `uv run whisprlinux service logs` returns recent service output or a status fallback.
- [ ] `uv run whisprlinux service stop` stops the background listener.
