from whisprlinux.config import default_config
from whisprlinux.providers.registry import provider_for_config, provider_names


def test_fake_provider_registered(tmp_path) -> None:
    config = default_config().model_copy(update={"provider": "fake", "providers": {"fake": {"text": "hi"}}})
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"RIFF")
    assert "fake" in provider_names()
    assert provider_for_config(config).transcribe(audio, config).text == "hi"
