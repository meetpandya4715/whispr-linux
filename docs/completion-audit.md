# Completion Audit

Objective: implement `docs/plans/2026-05-10-whisprlinux-implementation-plan.md` end to end.

This audit maps the plan requirements to concrete artifacts and records which gates have current evidence.

## Implemented Artifacts

| Requirement | Evidence |
| --- | --- |
| Python package named `whisprlinux` | `pyproject.toml`, `src/whisprlinux/__init__.py` |
| CLI executable named `whisprlinux` | `pyproject.toml` console script points to `whisprlinux.cli:app` |
| Config defaults and commands | `src/whisprlinux/config.py`, `src/whisprlinux/cli.py`, `tests/test_config.py` |
| Config path `~/.config/whisprlinux/config.toml` | `config_path()` in `src/whisprlinux/config.py` |
| Keyring secret storage | `src/whisprlinux/secrets.py`, `tests/test_secrets.py` |
| Doctor diagnostics | `src/whisprlinux/doctor.py`, `tests/test_doctor.py` |
| PulseAudio recording through `parec` plus `ffmpeg` | `src/whisprlinux/audio.py`, `tests/test_audio.py` |
| Provider abstraction and OpenAI implementation | `src/whisprlinux/providers/base.py`, `src/whisprlinux/providers/openai.py`, `src/whisprlinux/providers/registry.py`, `tests/test_openai_provider.py`, `tests/test_provider_registry.py` |
| Clipboard and paste behavior | `src/whisprlinux/clipboard.py`, `tests/test_clipboard.py` |
| X11 hotkey parsing and state machine | `src/whisprlinux/input_x11.py`, `tests/test_input_x11.py`, `tests/test_hotkey_state.py` |
| Hold-to-talk daemon workflow | `src/whisprlinux/daemon.py`, `tests/test_daemon.py` |
| User service lifecycle | `src/whisprlinux/service.py`, `tests/test_service.py` |
| Provider extension docs | `docs/providers.md` |
| Manual live verification checklist | `docs/manual-verification.md` |
| Setup, security, troubleshooting, model switching docs | `README.md` |
| Ignore local secrets and generated files | `.gitignore` includes `.env`, `.venv/`, caches, audio, logs, and build output |

## Fresh Verification Commands

Run these before claiming completion:

```bash
uv run pytest -v
uv run whisprlinux doctor
uv run whisprlinux auth status
uv run whisprlinux config show
uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav
file /tmp/whisprlinux-test.wav
uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav
uv run whisprlinux service status
git status --short --ignored
```

## Current Verified Status

- Unit coverage passes for implemented modules.
- Doctor verifies the local Ubuntu GNOME X11 session, PulseAudio tools, `parec`, `ffmpeg`, `xclip`, Pynput/X11 paste backend, keyring availability, and config readability.
- The OpenAI API key has been imported from ignored local `.env` into the desktop keyring.
- `auth test-openai-key` verifies the OpenAI API is reachable.
- `record-test` creates a 16-bit mono 16000 Hz WAV at `/tmp/whisprlinux-test.wav`.
- `transcribe-file /tmp/whisprlinux-test.wav` returned text through OpenAI.
- Clipboard-only output was verified with `paste-test "hello from whisprlinux"` followed by `xclip -selection clipboard -o`.
- User service installation and lifecycle commands have been exercised; the service is installed and currently stopped.
- `.env` is ignored and must not be committed or inspected as a source artifact.

## Remaining Gates

These gates cannot be honestly marked complete without live desktop interaction:

- `uv run whisprlinux daemon --foreground` plus holding the configured chord and confirming text appears in the active application
- `clipboard_and_paste` mode verified in a real text editor after OpenAI transcription succeeds

Completion status: incomplete until the remaining gates pass.
