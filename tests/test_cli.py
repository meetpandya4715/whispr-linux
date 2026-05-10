from typer.testing import CliRunner

from whisprlinux.cli import app


def test_cli_version() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "whisprlinux" in result.output


def test_transcribe_file_missing_key_is_clean_error(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    monkeypatch.setenv("WHISPRLINUX_CONFIG_DIR", str(config_dir))
    monkeypatch.setattr("whisprlinux.providers.openai.get_openai_key", lambda: None)
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    result = CliRunner().invoke(app, ["transcribe-file", str(audio)])
    assert result.exit_code == 1
    assert "OpenAI API key missing" in result.output
    assert "Traceback" not in result.output


def test_models_list_shows_transcription_models() -> None:
    result = CliRunner().invoke(app, ["models", "list"])
    assert result.exit_code == 0
    assert "gpt-4o-transcribe" in result.output
    assert "whisper-1" in result.output


def test_models_choose_sets_model_by_number(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    monkeypatch.setenv("WHISPRLINUX_CONFIG_DIR", str(config_dir))

    result = CliRunner().invoke(app, ["models", "choose", "--number", "2", "--no-restart"])

    assert result.exit_code == 0
    assert "Updated model" in result.output
    show = CliRunner().invoke(app, ["config", "show"])
    assert "model = \"whisper-1\"" in show.output
