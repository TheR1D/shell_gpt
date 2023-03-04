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
from typing import Callable

import typer

# Click is part of typer.
from click import MissingParameter, BadParameter
from rich.progress import Progress, SpinnerColumn, TextColumn
from sgpt import ChatGPT

DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "api_key.txt"
CURRENT_SHELL = "PowerShell" if platform.system() == "Windows" else "Bash"
CODE_PROMPT = "Provide code and only code as output without any additional text, prompt or note."
SHELL_PROMPT = f"Provide only {CURRENT_SHELL} command as output, without any additional text or prompt."


def get_api_key() -> str:
    """
    Retrieves API key from the file located in the user's home
    directory, or prompts the user to input it if it does not exist.

    :return: String API key for OpenAI API requests.
    """
    if not KEY_FILE.exists():
        api_key = getpass(prompt="Please enter your API secret key")
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(api_key)
    else:
        api_key = KEY_FILE.read_text().strip()
    return api_key


def loading_spinner(func: Callable) -> Callable:
    """
    Decorator that adds a loading spinner animation to a function that uses the OpenAI API.

    :param func: Function to wrap.
    :return: Wrapped function with loading.
    """
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner"):
            return func(*args, **kwargs)
        text = TextColumn("[green]Consulting with robots...")
        with Progress(SpinnerColumn(), text, transient=True) as progress:
            progress.add_task("request")
            return func(*args, **kwargs)
    return wrapper


def get_edited_prompt() -> str:
    """
    Opens the user's default editor to let them
    input a prompt, and returns the edited text.

    :return: String prompt.
    """
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
def get_completion(
    prompt: str,
    api_key: str,
    temperature: float,
    top_p: float,
    caching: bool,
    chat: str,
) -> str:
    """
    Generates completions for a given prompt using the OpenAI API.

    :param prompt: Prompt to generate completion for.
    :param api_key: OpenAI API key.
    :param temperature: Controls randomness of GPT-3.5 completions.
    :param top_p: Controls most probable tokens for completions.
    :param caching: Enable/Disable caching.
    :param chat: Enable/Disable conversation (chat mode).
    :return: GPT-3.5 generated completion.
    """
    chat_gpt = ChatGPT(api_key)
    model = "gpt-3.5-turbo"
    if not chat:
        return chat_gpt.get_completion(prompt, model, temperature, top_p, caching)
    return chat_gpt.get_chat_completion(
        model=model, temperature=temperature, top_probability=top_p, message=prompt, chat_id=chat
    )


def typer_writer(text: str, code: bool, shell: bool, animate: bool) -> None:
    """
    Writes output to the console, with optional typewriter animation and color.

    :param text: Text to output.
    :param code: If content of text is code.
    :param shell: if content of text is shell command.
    :param animate: Enable/Disable typewriter animation.
    :return: None
    """
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


def echo_chat_messages(chat_id: str) -> None:
    """
    Writes all messages from a specified chat ID to the console.

    :param chat_id: String chat id.
    :return: None
    """
    for index, message in enumerate(ChatGPT.chat_cache.get_messages(chat_id)):
        color = "cyan" if index % 2 == 0 else "green"
        typer.secho(message, fg=color)


def echo_chat_ids() -> None:
    """
    Writes all existing chat IDs to the console.

    :return: None
    """
    for chat_id in ChatGPT.chat_cache.get_chats():
        typer.echo(chat_id)


# Using lambda to pass a function to default value, which make it appear as "dynamic" in help.
def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    temperature: float = typer.Option(1.0, min=0.0, max=1.0, help="Randomness of generated output."),
    top_probability: float = typer.Option(1.0, min=0.1, max=1.0, help="Limits highest probable tokens (words)."),
    chat: str = typer.Option(None, help="Follow conversation with id (chat mode)."),
    show_chat: str = typer.Option(None, help="Show all messages from provided chat id."),
    list_chat: bool = typer.Option(False, help="List all existing chat ids."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    cache: bool = typer.Option(True, help="Cache completion results."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
) -> None:
    if list_chat:
        echo_chat_ids()
        return
    if show_chat:
        echo_chat_messages(show_chat)

    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    if editor:
        prompt = get_edited_prompt()

    if shell:
        # If probability and temperature were not changed (default), make response more accurate.
        if top_probability == 1 == temperature:
            temperature = 0.4
        prompt = f"{SHELL_PROMPT} {prompt}"
    elif code:
        prompt = f"{CODE_PROMPT} {prompt}"

    api_key = get_api_key()
    response_text = get_completion(
        prompt, api_key, temperature, top_probability, cache, chat, spinner=spinner
    )

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


def entry_point() -> None:
    """
    Python package entry point defined in setup.py

    :return: None
    """
    typer.run(main)


if __name__ == "__main__":
    entry_point()
