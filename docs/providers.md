# Provider Extension Guide

WhisprLinux keeps transcription providers behind a tiny protocol.

1. Create a module in `src/whisprlinux/providers/`.
2. Implement `transcribe(audio_path, config) -> TranscriptionResult`.
3. Register the provider with `register_provider("name", Provider())`.
4. Put provider-specific settings under `providers.<name>` in the config.
5. Add tests for request construction, error mapping, and registry lookup.

The built-in `fake` provider is for tests and local development:

```bash
uv run whisprlinux config set provider fake
uv run whisprlinux config set providers.fake.text "hello"
```
