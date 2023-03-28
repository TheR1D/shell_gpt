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
from typing import Mapping, List

import typer

# Click is part of typer.
from click import MissingParameter, BadParameter
from sgpt import config, make_prompt, OpenAIClient
from sgpt.utils import (
    echo_chat_ids,
    echo_chat_messages,
    get_edited_prompt,
)


def get_completion(
    messages: List[Mapping[str, str]],
    temperature: float,
    top_p: float,
    caching: bool,
    chat: str,
):
    api_host = config.get("OPENAI_API_HOST")
    api_key = config.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)
    return client.get_completion(
        messages=messages,
        model="gpt-3.5-turbo",
        temperature=temperature,
        top_probability=top_p,
        caching=caching,
        chat_id=chat,
    )


def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    temperature: float = typer.Option(1.0, min=0.0, max=1.0, help="Randomness of generated output."),
    top_probability: float = typer.Option(1.0, min=0.1, max=1.0, help="Limits highest probable tokens (words)."),
    chat: str = typer.Option(None, help="Follow conversation with id (chat mode)."),
    show_chat: str = typer.Option(None, help="Show all messages from provided chat id."),
    list_chat: bool = typer.Option(False, help="List all existing chat ids."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Generate and execute shell command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    cache: bool = typer.Option(True, help="Cache completion results."),
) -> None:
    if list_chat:
        echo_chat_ids()
        return
    if show_chat:
        echo_chat_messages(show_chat)
        return

    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    if editor:
        prompt = get_edited_prompt()

    prompt = make_prompt.initial(prompt, shell, code)

    if chat:
        initiated = bool(OpenAIClient.chat_cache.get_messages(chat))
        if initiated:
            if shell or code:
                raise BadParameter("Can't use --shell or --code for existing chat.")
            prompt = make_prompt.chat_mode(prompt, shell, code)

    completion = get_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_probability,
        caching=cache,
        chat=chat,
    )

    full_completion = ""
    for word in completion:
        typer.secho(word, fg="magenta", bold=True, nl=False)
        full_completion += word
    typer.secho()
    if not code and shell and typer.confirm("Execute shell command?"):
        os.system(full_completion)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
