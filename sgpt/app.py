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
import sys
import typer
import re
import subprocess

# Click is part of typer.
from click import MissingParameter
from sgpt import config, make_prompt, OpenAIClient
from sgpt.utils import (
    loading_spinner,
    echo_chat_ids,
    echo_chat_messages,
    typer_writer,
    get_edited_prompt,
)


@loading_spinner
def get_completion(
        role: str,
        prompt: str,
        temperature: float,
        top_p: float,
        model: str,
        caching: bool,
        chat: str,
):
    api_host = config.get("OPENAI_API_HOST")
    api_key = config.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)
    return client.get_completion(
        messages=prompt,
        model=model,
        temperature=temperature,
        top_probability=top_p,
        caching=caching,
        chat_id=chat,
        role=role
    )


def extract_command(text):
    pattern = r'```\s*(.*?)\s*```'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def main(
        prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
        temperature: float = typer.Option(1.0, min=0.0, max=1.0, help="Randomness of generated output."),
        top_probability: float = typer.Option(1.0, min=0.1, max=1.0, help="Limits highest probable tokens (words)."),
        role: str = typer.Option(None, help="Prompt portion for system role."),
        model: str = typer.Option(config.get("DEFAULT_MODEL"), help="Specify what model to use."),
        chat: str = typer.Option(None, help="Follow conversation with id (chat mode)."),
        show_chat: str = typer.Option(None, help="Show all messages from provided chat id."),
        list_chat: bool = typer.Option(False, help="List all existing chat ids."),
        shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
        execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
        interactive_execute: bool = typer.Option(False, help="Experimental interactive shell execution."),
        code: bool = typer.Option(False, help="Provide code as output."),
        editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
        cache: bool = typer.Option(True, help="Cache completion results."),
        animation: bool = typer.Option(True, help="Typewriter animation."),
        spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
) -> None:
    execute_core(prompt, temperature, top_probability, role, model, chat, show_chat, list_chat, shell, execute,
                 interactive_execute, code, editor, cache, animation, spinner)


def execute_core(prompt, temperature=1.0, top_probability=1.0, role=None, model=config.get("DEFAULT_MODEL"), chat=None,
                 show_chat=None, list_chat=False, shell=False, execute=False,
                 interactive_execute=False, code=False, editor=False, cache=True, animation=True, spinner=True):
    if list_chat:
        echo_chat_ids()
        return
    if show_chat:
        echo_chat_messages(show_chat)
        return

    if not prompt and not editor:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read()
        else:
            raise MissingParameter(param_hint="PROMPT", param_type="string")
    elif prompt and not sys.stdin.isatty():
        stdin_data = sys.stdin.read()
        prompt = f"{stdin_data.strip()}\n{prompt}"

    if editor:
        prompt = get_edited_prompt()

    if shell:
        if role:
            raise typer.BadParameter("Cannot use --role with --shell.")
        # If default values, make response more accurate.
        if top_probability == 1 == temperature:
            temperature = 0.4
        role, prompt = make_prompt.shell(prompt)
    elif code:
        if role:
            raise typer.BadParameter("Cannot use --role with --code.")
        role, prompt = make_prompt.code(prompt)

    if interactive_execute:
        if shell:
            raise typer.BadParameter("Cannot use --interactive-execute without --shell.")
        if execute:
            raise typer.BadParameter("Cannot use --interactive-execute without --execute.")
        if code:
            raise typer.BadParameter("Cannot use --interactive-execute without --code.")
        if role:
            raise typer.BadParameter("Cannot use --role with --interactive-execute.")
        role, prompt = make_prompt.interactive_execute(prompt)

        if not chat:
            chat = "interactive_execute" + str(os.getpid())

    completion = get_completion(
        role, prompt, temperature, top_probability, model, cache, chat, spinner=spinner
    )

    typer_writer(completion, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(completion)

    if interactive_execute:
        # check if completion contains a shell command
        command = extract_command(completion)
        if command:
            if typer.confirm(f"The assistant has requested to run the following command: ```{command}``` Run?"):
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                output = result.stdout
                errors = result.stderr
                new_prompt = f"Command executed: {command}\n\nResult stdout: \n{output}\nResult stderr: \n{errors}"
                if typer.confirm(
                        f"Would you like to continue the conversation with the following prompt: \n\"\"\"\n{new_prompt}\"\"\"\n\nContinue?"):
                    execute_core(new_prompt, interactive_execute=True, chat=chat, editor=editor, cache=cache,
                                 animation=animation, spinner=spinner)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
