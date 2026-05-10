# WhisprLinux

WhisprLinux is a lightweight Ubuntu/X11 hold-to-dictate utility. Hold a global hotkey, speak, release, and the transcription is copied to your clipboard or pasted into the active cursor.

It is designed for people who want Wispr Flow-style dictation on Linux without running local Whisper on a weak CPU. Audio is recorded locally, sent to OpenAI for transcription, then discarded unless debug audio retention is enabled.

## Features

- Hold-to-dictate global hotkey on X11
- OpenAI cloud transcription, including `gpt-4o-transcribe` and `gpt-4o-mini-transcribe`
- Clipboard-only, paste-at-cursor, and stdout output modes
- Paste handling for browsers, editors, Ghostty, and GNOME Terminal
- Subtle on-screen recording indicator while the hotkey is held
- User-level `systemd` service, no sudo required to run the daemon
- API key storage through the desktop keyring, with `OPENAI_API_KEY` fallback
- CLI diagnostics for microphone, X11, clipboard, keyring, and OpenAI connectivity

## Requirements

- Ubuntu or Ubuntu-based Linux desktop
- X11 session (`echo $XDG_SESSION_TYPE` should print `x11`)
- Python 3.13
- `uv`
- OpenAI API key with billing enabled
- System tools: `pactl`, `parec`, `ffmpeg`, and `xclip`
- Optional but recommended: Tk support for the on-screen recording indicator

Install the system tools:

```bash
sudo apt update
sudo apt install ffmpeg pulseaudio-utils xclip python3-tk
```

Install `uv` if you do not have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

```bash
git clone https://github.com/meetpandya4715/whispr-linux.git
cd whispr-linux

uv python install 3.13
uv sync

uv run whisprlinux doctor
uv run whisprlinux auth set-openai-key
uv run whisprlinux config set model gpt-4o-transcribe
uv run whisprlinux config set language en
uv run whisprlinux config set hotkey ctrl+super
uv run whisprlinux config set output_mode clipboard_and_paste
uv run whisprlinux config set paste_strategy auto
uv run whisprlinux config set recording_indicator true

uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav
uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav

uv run whisprlinux service install
uv run whisprlinux service start
```

To dictate, focus any text field, hold `Ctrl+Super`, speak, then release. If your first recording is too short, hold the hotkey a little longer before releasing.

## Service Commands

```bash
uv run whisprlinux service start
uv run whisprlinux service stop
uv run whisprlinux service restart
uv run whisprlinux service status
uv run whisprlinux service logs
uv run whisprlinux service uninstall
```

After changing configuration, restart the service:

```bash
uv run whisprlinux service restart
```

## Configuration

Config lives at `~/.config/whisprlinux/config.toml`.

```bash
uv run whisprlinux config show
uv run whisprlinux config set hotkey ctrl+alt+space
uv run whisprlinux config set language en
uv run whisprlinux config set output_mode clipboard
uv run whisprlinux config set output_mode clipboard_and_paste
uv run whisprlinux config set output_mode stdout
uv run whisprlinux config set paste_strategy auto
uv run whisprlinux config set recording_indicator true
```

Useful output modes:

- `clipboard_and_paste`: copy the transcript and paste it at the active cursor
- `clipboard`: only copy the transcript
- `stdout`: print the transcript, useful for debugging

Paste strategies:

- `auto`: use `Ctrl+V` in browsers/editors and `Ctrl+Shift+V` in terminals
- `ctrl_v`: always use `Ctrl+V`
- `ctrl_shift_v`: always use `Ctrl+Shift+V`
- `shift_insert`: use `Shift+Insert`, useful for Ghostty/GNOME Terminal edge cases

`recording_indicator = true` shows a small, subtle `Dictating...` popup near the bottom of the screen while the hotkey is held. If Tk is not available, dictation still works without the visual indicator.

If terminal paste does not work:

```bash
uv run whisprlinux config set paste_strategy shift_insert
uv run whisprlinux service restart
```

## Models and Pricing

```bash
uv run whisprlinux models list
uv run whisprlinux models choose
```

| Model | Estimated transcription price | Notes |
| --- | ---: | --- |
| `gpt-4o-transcribe` | `$0.006/min` | High-quality default |
| `gpt-4o-mini-transcribe` | `$0.003/min` | Lower-cost option |
| `gpt-4o-transcribe-diarize` | `$0.006/min` | Speaker diarization |
| `whisper-1` | `$0.006/min` | Classic Whisper model |

Pricing is the public estimated transcription cost per minute. Check OpenAI pricing before heavy use because model pricing can change.

## API Key and Privacy

Store your API key in the desktop keyring:

```bash
uv run whisprlinux auth set-openai-key
uv run whisprlinux auth status
uv run whisprlinux auth test-openai-key
```

If keyring storage is unavailable, set `OPENAI_API_KEY` in the shell or service environment that starts WhisprLinux.

Audio is sent to OpenAI for transcription. Local temporary audio files are removed after transcription unless `debug_keep_audio = true` is set in the config.

## Troubleshooting

- Run `uv run whisprlinux doctor` first; it checks Python, X11, PulseAudio, `ffmpeg`, `xclip`, keyring, config, and API connectivity.
- Wayland is not supported yet. Log into an X11 session before using the daemon.
- `Fn` is usually not exposed as a bindable OS key. Use `ctrl+super`, `ctrl+alt+space`, or `shift+f9`.
- For microphone issues, run `pactl get-default-source` and `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav`.
- For paste failures, try `uv run whisprlinux config set output_mode clipboard` to confirm transcription works before debugging paste.
- For terminal paste failures, set `paste_strategy` to `shift_insert`.
- If the recording indicator does not appear, install `python3-tk`; dictation can still run without it.
- For API errors, run `uv run whisprlinux auth test-openai-key` and try a supported model.

## Development

```bash
uv sync
uv run pytest -v
uv run whisprlinux doctor
```

Manual verification steps live in `docs/manual-verification.md`.

## Status

This is an early Linux/X11 utility built for personal daily use. It works well on Ubuntu GNOME X11, but Wayland support and realtime streaming are future work.
