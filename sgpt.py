"""
shell-gpt: An interface to OpenAI's ChatGPT (GPT-3.5) API

This module provides a simple interface for OpenAI's ChatGPT API using Typer
as the command line interface. It supports different modes of output including
shell commands and code, and allows users to specify the desired OpenAI model
and length and other options of the output. Additionally, it supports executing
shell commands directly from the interface.

API Key is stored locally for easy use in future runs.
"""


import os
import platform
from time import sleep
from pathlib import Path
from getpass import getpass
from tempfile import NamedTemporaryFile

import typer
import requests

# Click is part of typer.
from click import MissingParameter, BadParameter
from rich.progress import Progress, SpinnerColumn, TextColumn


API_URL = "https://api.openai.com/v1/chat/completions"
DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "api_key.txt"


def get_api_key():
    if not KEY_FILE.exists():
        api_key = getpass(prompt="Please enter your API secret key")
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(api_key)
    else:
        api_key = KEY_FILE.read_text().strip()
    return api_key


def loading_spinner(func):
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner"):
            return func(*args, **kwargs)
        text = TextColumn("[green]Consulting with robots...")
        with Progress(SpinnerColumn(), text, transient=True) as progress:
            progress.add_task("request")
            return func(*args, **kwargs)

    return wrapper


def get_edited_prompt():
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        # Create file and store path.
        file_path = file.name
    editor = os.environ.get("EDITOR", "vim")
    # This will write text to file using $EDITOR.
    os.system(f"{editor} {file_path}")
    # Read file when editor is closed.
    with open(file_path, "r") as file:
        output = file.read()
    os.remove(file_path)
    if not output:
        raise BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output


@loading_spinner
def openai_request(prompt, api_key, temperature, top_p):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-3.5-turbo",
        "temperature": temperature,
        "top_p": top_p,
    }
    response = requests.post(API_URL, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def typer_writer(text, code, shell, animate):
    shell_or_code = shell or code
    color = "magenta" if shell_or_code else None
    if animate and not shell_or_code:
        for char in text:
            typer.secho(char, nl=False, fg=color, bold=shell_or_code)
            sleep(0.015)
        # Add new line at the end, to prevent % from appearing.
        typer.echo("")
        return
    typer.secho(text, fg=color, bold=shell_or_code)


# Using lambda to pass a function to default value, which make it appear as "dynamic" in help.
def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    temperature: float = typer.Option(1.0, min=0.0, max=1.0, help="Randomness of generated output."),
    top_probability: float = typer.Option(1.0, min=0.1, max=1.0, help="Limits highest probable tokens (words)."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
):
    api_key = get_api_key()
    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")
    if shell:
        # If probability and temperature were not changed (default), make response more accurate.
        if top_probability == 1 == temperature:
            temperature = 0.4
        current_shell = "PowerShell" if platform.system() == "Windows" else "Bash"
        prompt = f"""Provide only {current_shell} command as output, without any additional text or prompt.
        {prompt}"""
    elif code:
        prompt = f"""Provide code and only code as output without any additional text, prompt or note.
        {prompt}"""
    if editor:
        prompt = get_edited_prompt()
    response_text = openai_request(prompt, api_key, temperature, top_probability, spinner=spinner)
    # For some reason OpenAI returns several leading/trailing white spaces.
    response_text = response_text.strip()
    if code:
        # Responses from GPT-3.5 wrapped into Markdown code block.
        lines = response_text.split("\n")
        if lines[0].startswith("```"):
            del lines[0]
        if lines[-1].startswith("```"):
            del lines[-1]
        response_text = "\n".join(lines)
    typer_writer(response_text, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
