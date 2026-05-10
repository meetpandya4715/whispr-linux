# WhisprLinux Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-admin Ubuntu/X11 dictation utility that records while a configurable hotkey chord is held, sends audio to a configurable transcription provider, then copies and optionally pastes the returned text at the current cursor.

**Architecture:** Implement a Python CLI plus long-running user service. The daemon listens for global X11 key press/release events, captures microphone audio through installed PulseAudio tools, transcribes through a provider abstraction, writes text to the clipboard with `xclip`, and optionally simulates paste through X11 keyboard control. Configuration lives in the user's config directory and secrets live in the desktop keyring when available.

**Tech Stack:** Python 3.13, `uv`, Typer CLI, Pydantic config, HTTPX, Python Keyring, Pynput on X11, PulseAudio `parec`/`pactl`, `ffmpeg`, `xclip`, user `systemd`.

---

## Current System Findings

- Working directory: `/home/meetp/Projects/Personal/whisprLinux`
- Git: fresh repository on branch `main`
- Desktop: `ubuntu:GNOME`
- Session: `x11`
- Display: `:1`
- Audio stack: PulseAudio server 15.99.1 available through `pactl` and `parec`
- Default microphone source: `alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp_6__source`
- Available tools: `uv`, Python 3.13.5, `ffmpeg`, `arecord`, `pactl`, `parec`, `xclip`, `systemctl --user`
- Missing tools that the implementation should not require: `xdotool`, `xsel`, `xbindkeys`, `wl-copy`, `wtype`, `ydotool`, `dotool`
- Installed Python packages observed globally: `httpx`, `keyring`
- Missing Python packages to install into the project environment: `pynput`, `typer`, `pydantic`, `platformdirs`, `rich`

## Product Requirements

- Press and hold a configurable global hotkey chord to record.
- Stop recording when the chord is released.
- Transcribe recorded audio through OpenAI transcription APIs.
- Copy transcription result into the clipboard.
- Optionally paste transcription result into the active application.
- Keep API keys out of source files, logs, command history where possible, and config files.
- Make OpenAI transcription model easy to change from the CLI.
- Support provider abstraction so other transcription providers can be added later.
- Provide CLI commands for configuration, diagnostics, service lifecycle, and one-shot tests.
- Run without admin installation on the current Ubuntu/X11 system.
- Provide a user-level background service that works across normal desktop applications.
- Include setup guidance, prerequisites, and quick verification commands when dependencies are introduced.

## Questions For You Before Implementation

The implementation can proceed with the defaults below if you do not answer these before running `/goal`.

1. Preferred default hotkey:
   - Recommended default: `ctrl+super`
   - Note: `fn+space` is probably not usable because most keyboards do not expose `Fn` as an OS-level key.
2. Default output mode:
   - Recommended default: copy to clipboard and auto-paste with `ctrl+v`
   - Safer fallback: copy only, with paste disabled until tested.
3. Default OpenAI transcription model:
   - Recommended configurable default: `gpt-4o-transcribe`
   - Alternative to test: `whisper-1`
4. Audio submission format:
   - Recommended default: record to temporary WAV through `parec` and `ffmpeg`
   - Future optimization: compressed audio before upload if latency or bandwidth becomes a concern.
5. Service behavior on transcription failure:
   - Recommended default: leave clipboard unchanged and show a desktop notification if `notify-send` is available.

## Deliverables

- Python package named `whisprlinux`.
- CLI executable named `whisprlinux`.
- Daemon command that runs the global hold-to-dictate loop.
- Local config file under `~/.config/whisprlinux/config.toml`.
- Secret storage via desktop keyring using service name `whisprlinux` and username `openai_api_key`.
- User systemd service file under `~/.config/systemd/user/whisprlinux.service`.
- Provider interface with OpenAI implementation and a stub-friendly path for future providers.
- Diagnostics command that checks desktop/session, audio tools, clipboard tool, keyring, config, and API connectivity.
- Unit tests for config, provider behavior, audio command construction, clipboard/paste behavior, and hotkey state machine.
- Manual verification checklist for live microphone, hotkey capture, clipboard, paste, and service lifecycle.
- Concise README with setup, security notes, configuration, troubleshooting, and model switching examples.

## Proposed File Structure

- Create: `pyproject.toml`
  - Defines project metadata, CLI entrypoint, dependencies, and pytest config.
- Create: `README.md`
  - User setup, commands, security model, troubleshooting, and quick verification.
- Create: `src/whisprlinux/__init__.py`
  - Package version.
- Create: `src/whisprlinux/cli.py`
  - Typer CLI commands.
- Create: `src/whisprlinux/config.py`
  - Config schema, defaults, loading, saving, and path helpers.
- Create: `src/whisprlinux/secrets.py`
  - Keyring-backed secret get/set/delete and safe prompting.
- Create: `src/whisprlinux/doctor.py`
  - Environment diagnostics.
- Create: `src/whisprlinux/audio.py`
  - PulseAudio source detection and recording through `parec` plus `ffmpeg`.
- Create: `src/whisprlinux/providers/base.py`
  - Provider protocol and transcription result type.
- Create: `src/whisprlinux/providers/openai.py`
  - OpenAI transcription API client.
- Create: `src/whisprlinux/providers/registry.py`
  - Provider selection and future-provider extension point.
- Create: `src/whisprlinux/clipboard.py`
  - Clipboard write using `xclip`.
- Create: `src/whisprlinux/input_x11.py`
  - X11 hotkey listener and paste simulation using `pynput`.
- Create: `src/whisprlinux/daemon.py`
  - Main daemon loop and recording/transcription/paste workflow.
- Create: `src/whisprlinux/service.py`
  - User systemd unit generation and service command helpers.
- Create: `src/whisprlinux/notify.py`
  - Optional notification wrapper using `notify-send` when present.
- Create: `tests/`
  - Focused pytest coverage for each module.
- Create: `.gitignore`
  - Ignore `.venv`, caches, temp audio files, local logs, and build output.

## Dependency And Setup Plan

Use `uv` so installation stays local to the project and does not require admin privileges.

System prerequisites already present on this machine:

```bash
python3 --version
uv --version
pactl info
which parec
which ffmpeg
which xclip
systemctl --user --version
```

Project dependency setup:

```bash
uv init --package --name whisprlinux
uv add typer rich pydantic platformdirs httpx keyring pynput
uv add --dev pytest pytest-mock
uv run whisprlinux doctor
```

Expected verification:

```text
Python: ok
Session: x11 ok
PulseAudio: ok
Recorder: parec ok
Transcoder: ffmpeg ok
Clipboard: xclip ok
Keyring: available
Paste backend: pynput/x11 ok
```

## Implementation Tasks

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/whisprlinux/__init__.py`
- Create: `src/whisprlinux/cli.py`
- Create: `tests/test_cli.py`

- [ ] Initialize the Python package with `uv init --package --name whisprlinux`.
- [ ] Add runtime dependencies with `uv add typer rich pydantic platformdirs httpx keyring pynput`.
- [ ] Add test dependencies with `uv add --dev pytest pytest-mock`.
- [ ] Add the console script entrypoint `whisprlinux = "whisprlinux.cli:app"`.
- [ ] Add `.gitignore` entries for `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/`, `*.egg-info/`, `*.wav`, `*.raw`, and `*.log`.
- [ ] Implement a minimal `whisprlinux --version`.
- [ ] Add a smoke test for CLI startup.
- [ ] Run `uv run pytest`.
- [ ] Commit with `git add . && git commit -m "chore: scaffold whisprlinux package"`.

### Task 2: Configuration System

**Files:**
- Create: `src/whisprlinux/config.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_config.py`

- [ ] Define config defaults:
  - `provider = "openai"`
  - `model = "gpt-4o-transcribe"`
  - `hotkey = "ctrl+super"`
  - `output_mode = "clipboard_and_paste"`
  - `audio_source = null`
  - `sample_rate = 16000`
  - `channels = 1`
  - `recording_max_seconds = 120`
  - `language = null`
  - `prompt = null`
  - `paste_delay_ms = 120`
  - `notify = true`
- [ ] Store config at `~/.config/whisprlinux/config.toml`.
- [ ] Implement `config path`, `config show`, `config set KEY VALUE`, and `config reset`.
- [ ] Validate enum-like fields with clear error messages.
- [ ] Add tests for default config, saving/loading, nested path creation, and invalid values.
- [ ] Run `uv run pytest tests/test_config.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: add configuration management"`.

### Task 3: Secret Storage

**Files:**
- Create: `src/whisprlinux/secrets.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_secrets.py`

- [ ] Implement `auth set-openai-key` using `getpass.getpass()` so the key is not echoed.
- [ ] Store the key with Python Keyring under service `whisprlinux` and username `openai_api_key`.
- [ ] Implement `auth status`, `auth delete-openai-key`, and `auth test-openai-key`.
- [ ] Never print the raw key.
- [ ] If no keyring backend is usable, print a clear fallback instruction to set `OPENAI_API_KEY` only for the current shell session.
- [ ] Add tests with a fake keyring backend.
- [ ] Run `uv run pytest tests/test_secrets.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: store OpenAI key securely"`.

### Task 4: Doctor Diagnostics

**Files:**
- Create: `src/whisprlinux/doctor.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_doctor.py`

- [ ] Implement `whisprlinux doctor`.
- [ ] Check Python version, `XDG_SESSION_TYPE`, `DISPLAY`, `pactl`, `parec`, `ffmpeg`, `xclip`, keyring availability, config readability, and whether an API key is available.
- [ ] Mark X11 as supported and Wayland as unsupported for the first release.
- [ ] Print actionable setup commands for missing project dependencies.
- [ ] Add tests using mocked environment variables and command lookup.
- [ ] Run `uv run pytest tests/test_doctor.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: add environment diagnostics"`.

### Task 5: Audio Capture

**Files:**
- Create: `src/whisprlinux/audio.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_audio.py`

- [ ] Implement default source detection with `pactl get-default-source`.
- [ ] Implement `record_until_stopped()` using `parec` to capture raw microphone audio and `ffmpeg` to convert it into a temporary WAV file.
- [ ] Enforce `recording_max_seconds`.
- [ ] Clean up temporary raw files after conversion.
- [ ] Keep WAV files in a secure temporary directory and delete them after transcription unless debug mode is enabled.
- [ ] Add `whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav`.
- [ ] Add command-construction tests without requiring live audio.
- [ ] Run a manual check: `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav`.
- [ ] Commit with `git add . && git commit -m "feat: capture microphone audio"`.

### Task 6: Provider Interface And OpenAI Transcription

**Files:**
- Create: `src/whisprlinux/providers/base.py`
- Create: `src/whisprlinux/providers/openai.py`
- Create: `src/whisprlinux/providers/registry.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_openai_provider.py`

- [ ] Define a provider protocol with `transcribe(audio_path, config) -> TranscriptionResult`.
- [ ] Implement OpenAI multipart upload to the transcription endpoint using `httpx`.
- [ ] Read API key from keyring first, then `OPENAI_API_KEY`.
- [ ] Pass configurable `model`, `language`, and `prompt` when set.
- [ ] Return normalized text and raw metadata.
- [ ] Map provider errors into user-friendly exceptions without logging secrets.
- [ ] Add `whisprlinux transcribe-file PATH`.
- [ ] Add HTTP tests with mocked responses for success, auth failure, rate limit, and invalid model.
- [ ] Run `uv run pytest tests/test_openai_provider.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: add OpenAI transcription provider"`.

### Task 7: Clipboard And Paste

**Files:**
- Create: `src/whisprlinux/clipboard.py`
- Create: `src/whisprlinux/input_x11.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_clipboard.py`
- Test: `tests/test_input_x11.py`

- [ ] Implement clipboard writes through `xclip -selection clipboard`.
- [ ] Implement paste simulation with `pynput.keyboard.Controller`.
- [ ] Support `output_mode` values `clipboard`, `clipboard_and_paste`, and `stdout`.
- [ ] Add `whisprlinux paste-test "hello from whisprlinux"`.
- [ ] Add tests that mock subprocess and keyboard controller calls.
- [ ] Manually verify clipboard-only mode in a terminal or text editor.
- [ ] Manually verify paste mode in a text editor before enabling it by default.
- [ ] Commit with `git add . && git commit -m "feat: copy and paste transcription text"`.

### Task 8: Hold-To-Talk Hotkey Daemon

**Files:**
- Create: `src/whisprlinux/daemon.py`
- Modify: `src/whisprlinux/input_x11.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_daemon.py`
- Test: `tests/test_hotkey_state.py`

- [ ] Parse hotkey strings such as `ctrl+super`, `ctrl+alt+space`, and `shift+f9`.
- [ ] Implement an X11 global listener with `pynput.keyboard.Listener`.
- [ ] Start recording once the full chord is pressed.
- [ ] Stop recording when any key in the chord is released.
- [ ] Ignore repeats while recording.
- [ ] Send the completed audio file to the configured provider.
- [ ] Send successful text to the configured output mode.
- [ ] Handle empty audio, empty transcription, cancelled recordings, API errors, and paste failures.
- [ ] Add `whisprlinux daemon --foreground`.
- [ ] Add state-machine tests that simulate key press/release sequences.
- [ ] Run `uv run pytest tests/test_daemon.py tests/test_hotkey_state.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: add hold-to-talk daemon"`.

### Task 9: User Service Lifecycle

**Files:**
- Create: `src/whisprlinux/service.py`
- Modify: `src/whisprlinux/cli.py`
- Test: `tests/test_service.py`

- [ ] Generate `~/.config/systemd/user/whisprlinux.service`.
- [ ] Use `ExecStart` pointing to the project-managed command path chosen during implementation.
- [ ] Include environment values needed for X11 access, especially `DISPLAY=:1` and `XDG_SESSION_TYPE=x11` when detected.
- [ ] Implement `service install`, `service start`, `service stop`, `service restart`, `service status`, `service logs`, and `service uninstall`.
- [ ] Run `systemctl --user daemon-reload` after install/uninstall.
- [ ] Add tests for rendered service content.
- [ ] Manual verification:
  - `uv run whisprlinux service install`
  - `uv run whisprlinux service start`
  - `uv run whisprlinux service status`
  - `uv run whisprlinux service logs`
- [ ] Commit with `git add . && git commit -m "feat: add user service management"`.

### Task 10: Provider Extensibility

**Files:**
- Modify: `src/whisprlinux/providers/base.py`
- Modify: `src/whisprlinux/providers/registry.py`
- Create: `docs/providers.md`
- Test: `tests/test_provider_registry.py`

- [ ] Make provider registration explicit and small.
- [ ] Add provider config namespacing so future providers can have their own settings without disturbing OpenAI settings.
- [ ] Add a fake provider for tests and local development that returns deterministic text.
- [ ] Document how to add a new provider:
  - create provider module
  - implement protocol
  - register provider name
  - add provider-specific config
  - add tests
- [ ] Run `uv run pytest tests/test_provider_registry.py -v`.
- [ ] Commit with `git add . && git commit -m "feat: prepare provider extension points"`.

### Task 11: README And Setup Guidance

**Files:**
- Create: `README.md`

- [ ] Document no-admin install:

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

- [ ] Document model switching:

```bash
uv run whisprlinux config set model whisper-1
uv run whisprlinux config set model gpt-4o-transcribe
```

- [ ] Document output mode switching:

```bash
uv run whisprlinux config set output_mode clipboard
uv run whisprlinux config set output_mode clipboard_and_paste
uv run whisprlinux config set output_mode stdout
```

- [ ] Document known limitation: first release targets X11; Wayland support is future work.
- [ ] Document known limitation: `Fn` is usually not detectable as a bindable key.
- [ ] Document troubleshooting for microphone access, keyring issues, paste failures, and API errors.
- [ ] Commit with `git add README.md && git commit -m "docs: add setup and usage guide"`.

### Task 12: End-To-End Verification

**Files:**
- Modify only if verification exposes defects.

- [ ] Run all tests: `uv run pytest -v`.
- [ ] Run diagnostics: `uv run whisprlinux doctor`.
- [ ] Set OpenAI key: `uv run whisprlinux auth set-openai-key`.
- [ ] Record sample: `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav`.
- [ ] Transcribe sample: `uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav`.
- [ ] Clipboard test: `uv run whisprlinux paste-test "hello from whisprlinux"`.
- [ ] Foreground daemon test: `uv run whisprlinux daemon --foreground`.
- [ ] Hold configured hotkey, speak, release, and confirm text appears in the active app.
- [ ] Service test:

```bash
uv run whisprlinux service install
uv run whisprlinux service restart
uv run whisprlinux service status
uv run whisprlinux service logs
```

- [ ] Confirm no API key appears in config, logs, test output, git diff, or shell-visible command arguments.
- [ ] Commit final fixes with `git add . && git commit -m "test: verify whisprlinux end to end"`.

## Acceptance Criteria

- `uv run whisprlinux doctor` reports the current Ubuntu/X11 environment as supported.
- `uv run whisprlinux auth set-openai-key` stores the OpenAI key without printing it.
- `uv run whisprlinux config set model <model>` changes the model used by transcription.
- `uv run whisprlinux record-test --seconds 3 --out /tmp/whisprlinux-test.wav` creates a playable WAV file.
- `uv run whisprlinux transcribe-file /tmp/whisprlinux-test.wav` returns spoken text through OpenAI.
- `uv run whisprlinux daemon --foreground` records only while the configured chord is held.
- Releasing the hotkey copies text to the clipboard.
- In `clipboard_and_paste` mode, releasing the hotkey pastes text into the active cursor location.
- `uv run whisprlinux service install/start/stop/restart/status/logs` manages the user service without sudo.
- The implementation does not require `xdotool`, `xbindkeys`, `ydotool`, `wl-copy`, or admin package installation.
- Tests pass with `uv run pytest -v`.

## Security Requirements

- Never commit or write the API key to repository files.
- Prefer keyring storage over `.env` files.
- Allow `OPENAI_API_KEY` only as an explicit fallback.
- Redact authorization headers and keys in exceptions and logs.
- Store temporary audio in a secure temp directory.
- Delete temporary audio after successful transcription unless debug mode is explicitly enabled.
- Avoid logging raw transcription text by default because dictated content may be sensitive.

## Future Work

- Wayland support with a separate backend.
- Optional desktop tray indicator.
- Optional audible start/stop sounds.
- Optional local/offline transcription provider for stronger privacy on faster hardware.
- Additional cloud providers for quality, latency, and cost comparison.
- Streaming transcription if the provider supports it well enough for lower-latency paste.
