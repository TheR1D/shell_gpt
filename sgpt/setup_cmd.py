"""``sgpt setup`` — choose and manage the provider this CLI talks to."""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Any

import typer
from click import UsageError
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Column, Table

from . import providers
from .utils import cli_error

app = typer.Typer(
    add_completion=False,
    help="Configure the LLM provider (OpenAI, Anthropic, Gemini, DeepSeek, ...).",
)

CUSTOM = "custom"
TEST_TIMEOUT = 15


def _is_tty() -> bool:
    """Separate hook so tests can drive the wizard through CliRunner."""
    return sys.stdin.isatty()


def _console() -> Console:
    return Console()


DIALOG_STYLE = Style.from_dict(
    {
        "title": "#7aa2f7 bold",
        "sel": "bg:#7aa2f7 #16161e bold",
        "opt": "#c0caf5",
        "hint": "#565f89 italic",
    }
)


def _build_dialog(
    title: str,
    options: list[tuple[str, str]],
    input: Any = None,
    output: Any = None,
) -> Any:
    """A picker where Enter selects and Esc cancels — no OK/Cancel buttons."""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, Window
    from prompt_toolkit.layout.controls import FormattedTextControl

    index = {"value": 0}
    keys = KeyBindings()

    def render() -> Any:
        lines = [("class:title", f" {title}\n\n")]
        for position, (_value, label) in enumerate(options):
            if position == index["value"]:
                lines.append(("class:sel", f"  {label}  \n"))
            else:
                lines.append(("class:opt", f"  {label}  \n"))
        lines.append(("class:hint", "\n  up/down move - enter select - esc cancel"))
        return lines

    @keys.add("up")
    @keys.add("k")
    def _up(event: Any) -> None:
        index["value"] = (index["value"] - 1) % len(options)

    @keys.add("down")
    @keys.add("j")
    def _down(event: Any) -> None:
        index["value"] = (index["value"] + 1) % len(options)

    @keys.add("enter")
    def _accept(event: Any) -> None:
        event.app.exit(result=options[index["value"]][0])

    @keys.add("escape")
    @keys.add("c-c")
    def _cancel(event: Any) -> None:
        event.app.exit(result=None)

    body = Window(
        FormattedTextControl(render, focusable=True, show_cursor=False),
        height=len(options) + 4,
        always_hide_cursor=True,
    )
    return Application(
        layout=Layout(body, focused_element=body),
        key_bindings=keys,
        style=DIALOG_STYLE,
        full_screen=False,
        input=input,
        output=output,
    )


def _dialog(title: str, options: list[tuple[str, str]]) -> str | None:
    """Run the picker. Returns None when the console cannot host one."""
    if not options:
        return None
    try:
        picked = _build_dialog(title, options).run()
    except Exception:  # no usable console; the caller falls back to typing
        return None
    return None if picked is None else str(picked)


def _ask_preset() -> str:
    options = [
        (name, f"{name}  ({preset.model})")
        for name, preset in sorted(providers.PRESETS.items())
    ]
    options.append((CUSTOM, "custom  (your own base URL and model)"))
    picked = _dialog("Provider", options)
    if picked:
        return picked
    typer.echo("Presets: " + ", ".join(sorted(providers.PRESETS)) + f", {CUSTOM}")
    return str(typer.prompt("Provider", default="openai")).strip().lower()


def _ask_profile(title: str) -> str | None:
    saved = providers.profiles()
    if not saved:
        cli_error("No providers saved yet - run 'sgpt setup' first")
    picked = _dialog(
        title,
        [(name, f"{name}  ({item.model})") for name, item in sorted(saved.items())],
    )
    return picked


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """With no sub-command, run the wizard."""
    if ctx.invoked_subcommand is None:
        wizard()


@app.command("list")
def list_providers() -> None:
    """Show saved providers and mark the active one."""
    rows = providers.rows()
    if not rows:
        typer.echo("No providers saved yet. Run 'sgpt setup' to add one.")
        return
    console = _console()
    # A narrow terminal cannot show a readable base URL; drop the column
    # instead of wrapping it character by character.
    wide = console.width >= 100
    columns = [
        Column("name", no_wrap=True),
        Column("preset", no_wrap=True),
        Column("model", overflow="ellipsis", min_width=12),
    ]
    if wide:
        columns.append(Column("base URL", overflow="ellipsis", min_width=20))
    columns += [
        Column("key var", no_wrap=True),
        Column("key", no_wrap=True),
        Column("active", no_wrap=True),
    ]
    table = Table(
        *columns,
        show_edge=False,
        pad_edge=False,
        header_style="bold #7aa2f7",
    )
    for _name, _preset, _model, _base_url, _env, _key, is_active in rows:
        if _key in ("stored", "ok"):
            colour = "green"
        elif _key == "missing":
            colour = "yellow"
        else:
            colour = "dim"
        cells = [f"[bold]{_name}[/bold]", _preset, _model]
        if wide:
            cells.append(f"[dim]{_base_url}[/dim]")
        cells += [
            f"[dim]{_env}[/dim]",
            f"[{colour}]{_key}[/{colour}]",
            "[green]yes[/green]" if is_active else "",
        ]
        table.add_row(*cells)
    console.print(table)
    active = providers.active_name() or "none"
    console.print(f"[dim]{len(rows)} profile(s) - active: {active}[/dim]")


@app.command("use")
def use_provider(
    name: str | None = typer.Argument(None, help="Profile to activate.")
) -> None:
    """Activate a saved provider (arrow-key picker when no name is given)."""
    name = name or _ask_profile("Activate provider")
    if not name:
        typer.echo("Cancelled.")
        raise typer.Exit(1)
    try:
        providers.set_active(name)
    except UsageError as error:
        cli_error(error)
    model = providers.profiles()[name].model
    typer.echo(f"Active provider: {name}  ({model})")


@app.command("remove")
def remove_provider(
    name: str | None = typer.Argument(None, help="Profile to delete.")
) -> None:
    """Delete a saved provider (arrow-key picker when no name is given)."""
    name = name or _ask_profile("Delete provider")
    if not name:
        typer.echo("Cancelled.")
        raise typer.Exit(1)
    if not typer.confirm(f"Delete '{name}'?", default=False):
        typer.echo("Cancelled.")
        raise typer.Exit(1)
    try:
        providers.remove(name)
    except UsageError as error:
        cli_error(error)
    active = providers.active_name()
    typer.echo(
        f"Removed {name}."
        + (f" Active provider: {active}" if active else " No active provider.")
    )


@app.command("test")
def test_provider(
    name: str
    | None = typer.Argument(None, help="Profile to test (default: the active one).")
) -> None:
    """Send a one-token request to check the profile works."""
    try:
        provider = providers.resolve(name)
    except UsageError as error:
        cli_error(error)
    if not provider.api_key():
        typer.echo(
            f"{provider.api_key_env or 'the API key'} is not set. "
            "Run 'sgpt setup' to store one, or set the variable and retry.",
            err=True,
        )
        raise typer.Exit(2)
    console = _console()
    if _is_tty():
        with console.status(f"Testing {provider.name}..."):
            latency = _probe(provider)
    else:
        latency = _probe(provider)
    console.print(
        f"[green]OK[/green] {provider.name}: {provider.model} in {latency} ms"
    )


def _probe(provider: "providers.Provider") -> int:
    """One tiny completion against the provider, with a specific error per failure."""
    from openai import APIConnectionError, APIStatusError, OpenAI

    key = provider.api_key()
    if not key:
        raise typer.BadParameter(
            f"{provider.api_key_env or 'OPENAI_API_KEY'} is not set",
            param_hint="provider",
        )

    client = OpenAI(
        api_key=key, base_url=provider.base_url or None, timeout=TEST_TIMEOUT
    )
    started = time.perf_counter()
    try:
        client.chat.completions.create(
            model=provider.model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
    except APIStatusError as error:
        if error.status_code in (401, 403):
            raise typer.BadParameter(
                f"{provider.name}: key rejected ({error.status_code})",
                param_hint="provider",
            ) from error
        detail = str(getattr(error, "message", "") or error)[:160]
        raise typer.BadParameter(
            f"{provider.name}: HTTP {error.status_code} {detail}", param_hint="provider"
        ) from error
    except APIConnectionError as error:
        raise typer.BadParameter(
            f"{provider.name}: cannot reach {provider.base_url or 'the API'}",
            param_hint="provider",
        ) from error
    return int((time.perf_counter() - started) * 1000)


def _clean(value: str) -> str:
    """Drop quotes people paste along with a URL or model name."""
    return value.strip().strip('"').strip("'")


def _ask_credential(default_var: str) -> tuple[str | None, str | None]:
    """Ask for the key itself, or the name of the variable that holds it.

    Returns (api_key_env, api_key_value). A pasted key is stored in
    providers.json (0600 on POSIX) exactly like upstream stores OPENAI_API_KEY
    in .sgptrc; a variable name is recorded and checked instead.
    """
    while True:
        value = _clean(typer.prompt("API key (or the name of an env var)", default=""))
        if not value:
            continue
        # An env var name is upper case; a DeepSeek-style hex key is not.
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) and value.isupper():
            if not os.getenv(value):
                typer.echo(
                    f"{value} is not set. Set it and re-run 'sgpt setup test':\n"
                    f'  export {value}=...      (Windows: setx {value} "...")',
                    err=True,
                )
            return value, None
        if len(value) >= 16 and not any(char.isspace() for char in value):
            typer.echo("Key stored in providers.json for this profile.")
            return default_var, value
        typer.echo("Neither a key nor a variable name - try again (nothing was saved).")


def _ask_name(preset_name: str) -> str:
    """Profile name defaults to the preset; only ask when it would overwrite."""
    if preset_name not in providers.profiles():
        return preset_name
    if typer.confirm(
        f"A profile named '{preset_name}' exists. Overwrite it?", default=True
    ):
        return preset_name
    while True:
        name = _clean(typer.prompt("Profile name", default=f"{preset_name}-2")).lower()
        if providers.NAME_RE.match(name):
            return name
        typer.echo("Lowercase letters, digits, '-' or '_' (max 32).")


def wizard() -> None:
    """Ask for a provider, save it, and optionally check the key."""
    if not _is_tty():
        typer.echo(
            "No interactive terminal. Use 'sgpt setup use <name>' or 'sgpt setup test <name>'.",
            err=True,
        )
        raise typer.Exit(2)

    _console().print(
        Panel.fit(
            "[bold]Provider setup[/bold]\n[dim]Keys never leave this machine[/dim]",
            border_style="#7aa2f7",
        )
    )
    preset_name = _ask_preset()
    if preset_name != CUSTOM and preset_name not in providers.PRESETS:
        raise typer.BadParameter(
            f"Unknown provider '{preset_name}'", param_hint="provider"
        )

    preset = providers.PRESETS.get(preset_name)
    base_url = _clean(
        typer.prompt("Base URL", default=preset.base_url if preset else "")
    )
    model = _clean(typer.prompt("Model", default=preset.model if preset else ""))
    name = _ask_name(preset_name)

    api_key_env = None
    api_key_value = None
    if preset is None or preset.api_key_env:
        default_var = (preset.api_key_env if preset else None) or "API_KEY"
        api_key_env, api_key_value = _ask_credential(default_var)

    provider = providers.Provider(
        name=name,
        preset=preset_name,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        api_key_value=api_key_value,
    )
    providers.save(provider)
    typer.echo(f"Saved and activated '{name}'.")
    key_label = "stored in providers.json" if api_key_value else (api_key_env or "none")
    _console().print(
        Panel.fit(
            f"[bold]{name}[/bold]\n"
            f"model   {model}\n"
            f"base    {base_url}\n"
            f"key     {key_label}\n\n"
            f"[dim]next:[/dim] sgpt setup test",
            title="saved",
            border_style="green",
        )
    )

    if typer.confirm("Test it now?", default=True):
        try:
            latency = _probe(provider)
        except typer.BadParameter as error:
            typer.echo(f"Test failed - {error.message}")
        else:
            typer.echo(f"OK {provider.model} in {latency} ms")
