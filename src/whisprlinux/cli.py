from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .audio import record_for_seconds
from .clipboard import deliver_text
from .config import config_path, load_config, reset_config, save_config, set_config_value, to_toml
from .daemon import run_daemon
from .doctor import api_connectivity, run_checks
from .providers.registry import provider_for_config
from .secrets import delete_openai_key, get_openai_key, has_openai_key, set_openai_key
from .service import install_service, service_action, service_logs, service_path, uninstall_service


console = Console()
app = typer.Typer(no_args_is_help=True)
config_app = typer.Typer(help="Manage local configuration.")
auth_app = typer.Typer(help="Manage API credentials.")
service_app = typer.Typer(help="Manage the user systemd service.")
app.add_typer(config_app, name="config")
app.add_typer(auth_app, name="auth")
app.add_typer(service_app, name="service")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"whisprlinux {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True, help="Show version."),
) -> None:
    pass


@config_app.command("path")
def config_path_command() -> None:
    console.print(str(config_path()))


@config_app.command("show")
def config_show() -> None:
    console.print(to_toml(load_config()))


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    try:
        set_config_value(key, value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Updated {key}")


@config_app.command("reset")
def config_reset() -> None:
    path = reset_config()
    console.print(f"Reset config at {path}")


@auth_app.command("set-openai-key")
def auth_set_openai_key() -> None:
    try:
        set_openai_key()
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print("OpenAI API key stored in keyring.")


@auth_app.command("status")
def auth_status() -> None:
    console.print("OpenAI API key: available" if has_openai_key() else "OpenAI API key: missing")


@auth_app.command("delete-openai-key")
def auth_delete_openai_key() -> None:
    delete_openai_key()
    console.print("OpenAI API key deleted from keyring.")


@auth_app.command("test-openai-key")
def auth_test_openai_key() -> None:
    api_key = get_openai_key()
    if not api_key:
        raise click.ClickException("OpenAI API key missing.")
    check = api_connectivity(api_key)
    console.print(f"{check.name}: {'ok' if check.ok else 'fail'} - {check.detail}")
    if not check.ok:
        raise typer.Exit(1)


@app.command()
def doctor() -> None:
    checks = run_checks()
    table = Table("Check", "Status", "Detail")
    for check in checks:
        table.add_row(check.name, "ok" if check.ok else "fail", check.detail)
    console.print(table)
    if not all(check.ok for check in checks if check.name not in {"API key"}):
        console.print("Setup: uv sync && uv run whisprlinux doctor")
        raise typer.Exit(1)


@app.command("record-test")
def record_test(seconds: int = typer.Option(3, min=1), out: Path = typer.Option(Path("/tmp/whisprlinux-test.wav"))) -> None:
    try:
        path = record_for_seconds(seconds, out, load_config())
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(str(path))


@app.command("transcribe-file")
def transcribe_file(path: Path) -> None:
    config = load_config()
    try:
        result = provider_for_config(config).transcribe(path, config)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(result.text)


@app.command("paste-test")
def paste_test(text: str) -> None:
    try:
        deliver_text(text, load_config())
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    console.print("Delivered text.")


@app.command()
def daemon(foreground: bool = typer.Option(False, "--foreground")) -> None:
    run_daemon(foreground)


@service_app.command("install")
def service_install() -> None:
    console.print(str(install_service()))


@service_app.command("uninstall")
def service_uninstall() -> None:
    uninstall_service()
    console.print(f"Removed {service_path()}")


@service_app.command("start")
def service_start() -> None:
    raise typer.Exit(service_action("start").returncode)


@service_app.command("stop")
def service_stop() -> None:
    raise typer.Exit(service_action("stop").returncode)


@service_app.command("restart")
def service_restart() -> None:
    raise typer.Exit(service_action("restart").returncode)


@service_app.command("status")
def service_status() -> None:
    raise typer.Exit(service_action("status").returncode)


@service_app.command("logs")
def service_logs_command() -> None:
    raise typer.Exit(service_logs().returncode)
