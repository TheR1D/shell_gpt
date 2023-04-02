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

import typer

# Click is part of typer.
from click import MissingParameter, BadArgumentUsage
from sgpt import config, OpenAIClient
from sgpt import ChatHandler, DefaultHandler
from sgpt.utils import get_edited_prompt


def main(  # pylint: disable=too-many-arguments
    prompt: str = typer.Argument(
        None,
        show_default=False,
        help="The prompt to generate completions for.",
    ),
    temperature: float = typer.Option(
        0.1,
        min=0.0,
        max=1.0,
        help="Randomness of generated output.",
    ),
    top_probability: float = typer.Option(
        1.0,
        min=0.1,
        max=1.0,
        help="Limits highest probable tokens (words).",
    ),
    chat: str = typer.Option(
        None,
        help="Follow conversation with id (chat mode).",
        rich_help_panel="Chat Options",
    ),
    show_chat: str = typer.Option(  # pylint: disable=W0613
        None,
        help="Show all messages from provided chat id.",
        callback=ChatHandler.show_messages,
        rich_help_panel="Chat Options",
    ),
    list_chat: bool = typer.Option(  # pylint: disable=W0613
        False,
        help="List all existing chat ids.",
        callback=ChatHandler.list_ids,
        rich_help_panel="Chat Options",
    ),
    shell: bool = typer.Option(
        False,
        "--shell",
        "-s",
        help="Generate and execute shell commands.",
        rich_help_panel="Assistance Options",
    ),
    code: bool = typer.Option(
        False,
        help="Generate only code.",
        rich_help_panel="Assistance Options",
    ),
    editor: bool = typer.Option(
        False,
        help="Open $EDITOR to provide a prompt.",
    ),
    cache: bool = typer.Option(
        True,
        help="Cache completion results.",
    ),
    model: str = typer.Option(
        os.getenv("MODEL", "gpt-3.5-turbo"),
        help="The OpenAI model which will generate the completion."
    ),
) -> None:
    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    if shell and code:
        raise BadArgumentUsage("--shell and --code options cannot be used together.")

    if editor:
        prompt = get_edited_prompt()

    api_host = config.get("OPENAI_API_HOST")
    api_key = config.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)

    if chat:
        full_completion = ChatHandler(client, chat, shell, code).handle(
            prompt,
            temperature=temperature,
            top_probability=top_probability,
            chat_id=chat,
            caching=cache,
            model=model,
        )
    else:
        full_completion = DefaultHandler(client, shell, code).handle(
            prompt,
            temperature=temperature,
            top_probability=top_probability,
            caching=cache,
            model=model,
        )

    if not code and shell and typer.confirm("Execute shell command?"):
        os.system(full_completion)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
