import os
from time import sleep
from typing import Callable
from tempfile import NamedTemporaryFile
import subprocess

import typer
from typing import Tuple

from click import BadParameter
from rich.progress import Progress, SpinnerColumn, TextColumn
from sgpt import OpenAIClient
import select


# convert to a class
class Colors:
    red = "\033[31m"
    green = "\033[32m"
    cyan = "\033[36m"
    reset = "\033[0m"


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


def get_edited_prompt(edit_starting_text) -> str:
    """
    Opens the user's default editor to let them
    input a prompt, and returns the edited text.

    :return: String prompt.
    """
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        # Create file and store path.
        file_path = file.name
        # Write starting text to file.
        file.write(edit_starting_text.encode())
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


def typer_writer(text: str, code: bool, shell: bool, interactive_execute: bool, animate: bool) -> None:
    """
    Writes output to the console, with optional typewriter animation and color.

    :param text: Text to output.
    :param code: If content of text is code.
    :param shell: if content of text is shell command.
    :param interactive_execute: If content of text is interactive execute.
    :param animate: Enable/Disable typewriter animation.
    :return: None
    """
    shell_or_code = shell or code or interactive_execute
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
    # Prints all messages from a specified chat ID to the console.
    for index, message in enumerate(OpenAIClient.chat_cache.show(chat_id)):
        color = "cyan" if index % 2 == 0 else "green"
        typer.secho(message, fg=color)


def echo_chat_ids() -> None:
    # Prints all existing chat IDs to the console.
    for chat_id in OpenAIClient.chat_cache.list():
        typer.echo(chat_id)


def run_command_with_realtime_output(command: str) -> Tuple[int, str, str]:
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True
    )

    # Initialize variables to store complete stdout and stderr
    full_stdout = ""
    full_stderr = ""

    while True:
        # Check if either stdout or stderr has data available
        ready_streams, _, _ = select.select([process.stdout, process.stderr], [], [])

        for stream in ready_streams:
            if stream == process.stdout:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    print(f"{Colors.cyan}{stdout_line.strip()}{Colors.reset}")
                    full_stdout += stdout_line
            elif stream == process.stderr:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    print(f"{Colors.red}{stderr_line.strip()}{Colors.reset}")
                    full_stderr += stderr_line

        return_code = process.poll()
        if return_code is not None:
            break

    # Return the exit code of the shell command along with the full stdout and stderr
    return return_code, full_stdout, full_stderr

