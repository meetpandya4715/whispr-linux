# WhisprLinux

WhisprLinux is a no-admin Ubuntu/X11 hold-to-dictate utility. Hold a configurable hotkey, speak, release, and the transcription is copied to the clipboard or pasted at the active cursor.

## Setup

System prerequisites: Python 3.13, `uv`, PulseAudio tools (`pactl`, `parec`), `ffmpeg`, `xclip`, X11, and user `systemd`.

```bash
uv sync
uv run whisprlinux doctor
uv run whisprlinux auth set-openai-key
uv run whisprlinux config set model gpt-4o-transcribe
uv run whisprlinux config set hotkey ctrl+super
uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav
uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav
uv run whisprlinux service install
uv run whisprlinux service start
```

Quick verification:

```bash
uv run pytest -v
uv run whisprlinux doctor
```

For the full live test flow, use `docs/manual-verification.md` after storing a real OpenAI API key.

## Configuration

Config lives at `~/.config/whisprlinux/config.toml`.

```bash
uv run whisprlinux config show
uv run whisprlinux config set model whisper-1
uv run whisprlinux config set model gpt-4o-transcribe
uv run whisprlinux models list
uv run whisprlinux models choose
uv run whisprlinux config set output_mode clipboard
uv run whisprlinux config set output_mode clipboard_and_paste
uv run whisprlinux config set output_mode stdout
uv run whisprlinux config set paste_strategy auto
```

`paste_strategy = "auto"` uses `Ctrl+V` in browsers and editors, and `Ctrl+Shift+V` in terminal windows such as Ghostty and GNOME Terminal. You can force either behavior with `ctrl_v` or `ctrl_shift_v`.
If terminal paste still does not trigger, use `shift_insert`, which many terminals and text fields accept:

```bash
uv run whisprlinux config set paste_strategy shift_insert
uv run whisprlinux service restart
```

Secrets are stored through the desktop keyring using service `whisprlinux` and username `openai_api_key`. If no keyring is available, use `OPENAI_API_KEY` only for the current shell session.

## Service

```bash
uv run whisprlinux service install
uv run whisprlinux service start
uv run whisprlinux service status
uv run whisprlinux service logs
uv run whisprlinux service stop
uv run whisprlinux service uninstall
```

## Troubleshooting

- First release targets X11. Wayland support is future work.
- `Fn` is usually not exposed as a bindable OS key; use `ctrl+super`, `ctrl+alt+space`, or `shift+f9`.
- For microphone issues, run `pactl get-default-source` and `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav`.
- For keyring issues, run `uv run whisprlinux auth status` and set `OPENAI_API_KEY` only in the shell that needs it.
- For paste failures, switch to `uv run whisprlinux config set output_mode clipboard` and test with `xclip`.
- For API errors, run `uv run whisprlinux auth test-openai-key` and try a supported model.
