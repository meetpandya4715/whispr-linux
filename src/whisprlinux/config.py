from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, Literal

from platformdirs import user_config_dir
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


ProviderName = Literal["openai", "fake"]
OutputMode = Literal["clipboard", "clipboard_and_paste", "stdout"]
PasteStrategy = Literal["auto", "ctrl_v", "ctrl_shift_v", "shift_insert"]


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: ProviderName = "openai"
    model: str = "gpt-4o-transcribe"
    hotkey: str = "ctrl+super"
    output_mode: OutputMode = "clipboard_and_paste"
    audio_source: str | None = None
    sample_rate: int = 16000
    channels: int = 1
    recording_max_seconds: int = 120
    recording_tail_padding_ms: int = 450
    language: str | None = None
    prompt: str | None = None
    paste_delay_ms: int = 120
    paste_strategy: PasteStrategy = "auto"
    notify: bool = True
    recording_indicator: bool = True
    debug_keep_audio: bool = False
    providers: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("sample_rate", "channels", "recording_max_seconds", "recording_tail_padding_ms", "paste_delay_ms")
    @classmethod
    def positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("hotkey")
    @classmethod
    def hotkey_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("hotkey must not be empty")
        return value.strip().lower()

    @field_validator("audio_source", "language", "prompt", mode="before")
    @classmethod
    def empty_string_is_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


def config_dir() -> Path:
    override = os.environ.get("WHISPRLINUX_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path(user_config_dir("whisprlinux"))


def config_path() -> Path:
    return config_dir() / "config.toml"


def default_config() -> AppConfig:
    return AppConfig()


def load_config(path: Path | None = None) -> AppConfig:
    path = path or config_path()
    if not path.exists():
        return default_config()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_toml(config.model_dump()), encoding="utf-8")
    path.chmod(0o600)
    return path


def reset_config(path: Path | None = None) -> Path:
    return save_config(default_config(), path)


def parse_value(raw: str) -> Any:
    value = raw.strip()
    lowered = value.lower()
    if lowered in {"null", "none"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        return value


def set_config_value(key: str, raw_value: str, path: Path | None = None) -> AppConfig:
    key = key.strip()
    config = load_config(path)
    data = config.model_dump()
    if "." in key:
        parts = key.split(".")
        cursor: dict[str, Any] = data
        for part in parts[:-1]:
            next_value = cursor.setdefault(part, {})
            if not isinstance(next_value, dict):
                raise ValueError(f"{part} is not a nested config object")
            cursor = next_value
        cursor[parts[-1]] = parse_value(raw_value)
    elif key in data:
        data[key] = parse_value(raw_value)
    else:
        raise ValueError(f"Unknown config key: {key}")
    try:
        updated = AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    save_config(updated, path)
    return updated


def to_toml(data: dict[str, Any] | AppConfig) -> str:
    if isinstance(data, AppConfig):
        data = data.model_dump()
    return _format_mapping(data, include_none=False)


def format_config(data: dict[str, Any] | AppConfig) -> str:
    if isinstance(data, AppConfig):
        data = data.model_dump()
    return _format_mapping(data, include_none=True)


def _format_mapping(data: dict[str, Any], *, include_none: bool) -> str:
    lines: list[str] = []
    nested: list[tuple[str, dict[str, Any]]] = []
    for key, value in data.items():
        if value is None and not include_none:
            continue
        if isinstance(value, dict):
            nested.append((key, value))
        else:
            lines.append(f"{key} = {_format_toml(value, include_none=include_none)}")
    for section, values in nested:
        if not values:
            lines.append(f"{section} = {{}}")
            continue
        lines.append("")
        _write_section(lines, section, values, include_none=include_none)
    return "\n".join(lines).strip() + "\n"


def _write_section(lines: list[str], name: str, values: dict[str, Any], *, include_none: bool) -> None:
    scalar = {k: v for k, v in values.items() if not isinstance(v, dict) and (v is not None or include_none)}
    nested = {k: v for k, v in values.items() if isinstance(v, dict)}
    if scalar:
        lines.append(f"[{name}]")
        for key, value in scalar.items():
            lines.append(f"{key} = {_format_toml(value, include_none=include_none)}")
    for key, value in nested.items():
        lines.append(f"[{name}.{key}]")
        for sub_key, sub_value in value.items():
            if sub_value is None and not include_none:
                continue
            lines.append(f"{sub_key} = {_format_toml(sub_value, include_none=include_none)}")


def _format_toml(value: Any, *, include_none: bool) -> str:
    if value is None:
        if include_none:
            return "null"
        raise TypeError("None values cannot be written to TOML")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(f"Unsupported TOML value: {value!r}")
