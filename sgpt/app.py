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
from click import MissingParameter
from sgpt import config, make_prompt, OpenAIClient
from sgpt.utils import (
    loading_spinner,
    echo_chat_ids,
    echo_chat_messages,
    typer_writer,
    get_edited_prompt,
    combine_with_stdin_prompt
)


@loading_spinner
def get_completion(
    prompt: str,
    temperature: float,
    top_p: float,
    caching: bool,
    chat: str,
):
    api_host = config.get("OPENAI_API_HOST")
    api_key = config.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)
    return client.get_completion(
        message=prompt,
        model="gpt-3.5-turbo",
        temperature=temperature,
        top_probability=top_p,
        caching=caching,
        chat_id=chat,
    )


def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    stdin_before: bool = typer.Option(False, help="Place stdin before after prompt argument, default is to place it after."),
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
        return
    
    prompt = combine_with_stdin_prompt(prompt,stdin_before)

    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    if editor:
        prompt = get_edited_prompt(prompt)

    if shell:
        # If default values, make response more accurate.
        if top_probability == 1 == temperature:
            temperature = 0.4
        prompt = make_prompt.shell(prompt)
    elif code:
        prompt = make_prompt.code(prompt)

    completion = get_completion(
        prompt, temperature, top_probability, cache, chat, spinner=spinner
    )

    typer_writer(completion, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(completion)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
