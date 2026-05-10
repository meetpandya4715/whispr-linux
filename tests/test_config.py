from pathlib import Path

import pytest

from whisprlinux.config import default_config, format_config, load_config, save_config, set_config_value


def test_default_config() -> None:
    config = default_config()
    assert config.provider == "openai"
    assert config.model == "gpt-4o-transcribe"
    assert config.hotkey == "ctrl+super"
    assert config.output_mode == "clipboard_and_paste"
    assert config.paste_strategy == "auto"
    assert config.recording_indicator is True


def test_save_load_and_nested_creation(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "config.toml"
    save_config(default_config(), path)
    assert path.exists()
    assert 'audio_source = ""' not in path.read_text()
    assert load_config(path).sample_rate == 16000
    assert load_config(path).audio_source is None


def test_format_config_shows_null_defaults() -> None:
    rendered = format_config(default_config())
    assert "audio_source = null" in rendered
    assert "language = null" in rendered
    assert "prompt = null" in rendered


def test_set_config_value(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    save_config(default_config(), path)
    config = set_config_value("model", "whisper-1", path)
    assert config.model == "whisper-1"


def test_set_nested_provider_value(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    save_config(default_config(), path)
    set_config_value("providers.fake.text", "hello", path)
    assert load_config(path).providers["fake"]["text"] == "hello"
    assert "[providers.fake]" in path.read_text()


def test_invalid_enum_value(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    save_config(default_config(), path)
    with pytest.raises(ValueError):
        set_config_value("output_mode", "telepathy", path)
