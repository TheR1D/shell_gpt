"""
shell-gpt: An interface to OpenAI's GPT-3 API

This module provides a simple interface for OpenAI's GPT-3 API using Typer
as the command line interface. It supports different modes of output including
shell commands and code, and allows users to specify the desired OpenAI model
and length of the output. Additionally, it supports executing shell
commands directly from the interface.

API Key is stored locally for easy use in future runs.
"""

# pylint: disable=missing-function-docstring,too-many-arguments

import os
from time import sleep
from pathlib import Path
from getpass import getpass

import typer
import requests
from rich.progress import Progress, SpinnerColumn, TextColumn


API_URL = "https://api.openai.com/v1/completions"
DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "api_key.txt"


def get_api_key():
    if not KEY_FILE.exists():
        api_key = getpass(prompt="Please enter your API secret key")
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(api_key)
    else:
        api_key = KEY_FILE.read_text()
    return api_key


def loading_spinner(func):
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner"):
            return func(*args, **kwargs)
        text = TextColumn("[green]Requesting OpenAI...")
        with Progress(SpinnerColumn(), text, transient=True) as progress:
            progress.add_task("request")
            return func(*args, **kwargs)

    return wrapper


@loading_spinner
def openai_request(prompt, model, max_tokens, api_key):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "prompt": prompt,
        "model": model,
        "max_tokens": max_tokens,
    }
    response = requests.post(API_URL, headers=headers, json=data, timeout=5)
    response.raise_for_status()
    return response.json()["choices"][0]["text"]


def typer_writer(text, code, shell, animate):
    shell_or_code = shell or code
    color = "magenta" if shell_or_code else None
    # typer.colors.
    if animate and not shell_or_code:
        for char in text:
            typer.secho(char, nl=False, fg=color, bold=shell_or_code)
            sleep(0.015)
        # Add new line at the end, to prevent % from appearing.
        typer.echo("")
        return
    typer.secho(text, fg=color, bold=shell_or_code)


def main(
    prompt: str,
    model: str = typer.Option("text-davinci-003", help="OpenAI model name."),
    max_tokens: int = typer.Option(2048, help="Strict length of output (words)."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
):
    api_key = get_api_key()
    if shell:
        prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        prompt = f"{prompt}. Provide only code as output."
    response_text = openai_request(prompt, model, max_tokens, api_key, spinner=spinner)
    # For some reason OpenAI returns several leading/trailing white spaces.
    response_text = response_text.strip()
    typer_writer(response_text, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
