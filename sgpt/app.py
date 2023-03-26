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
from click import MissingParameter
from sgpt import config, make_prompt, OpenAIClient
from sgpt.utils import (
    echo_chat_ids,
    echo_chat_messages,
    typer_writer,
    get_edited_prompt,
)


def get_completion(
    message: List[Mapping[str, str]],
    temperature: float,
    top_p: float,
    caching: bool,
    chat: str,
):
    api_host = config.get("OPENAI_API_HOST")
    api_key = config.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)
    return client.get_completion(
        message=message,
        model="gpt-3.5-turbo",
        temperature=temperature,
        top_probability=top_p,
        caching=caching,
        chat_id=chat,
    )


def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    temperature: float = typer.Option(0.0, min=0.0, max=1.0, help="Randomness of generated output."),
    top_probability: float = typer.Option(1.0, min=0.1, max=1.0, help="Limits highest probable tokens (words)."),
    chat: str = typer.Option(None, help="Follow conversation with id (chat mode)."),
    show_chat: str = typer.Option(None, help="Show all messages from provided chat id."),
    list_chat: bool = typer.Option(False, help="List all existing chat ids."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
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

    if code:
        result = make_prompt.code(prompt)
    else:
        result = make_prompt.shell(prompt)

    completion = get_completion(
        [
            {'role': 'system', 'content': result['system']},
            {'role': 'user', 'content': result['user']},
        ],
        temperature, top_probability, cache, chat
    )

    full_completion = ''
    for i in completion:
        typer_writer(i, True)
        full_completion += i
    print()
    if not code and execute and typer.confirm("Execute shell command?"):
        os.system(full_completion)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
