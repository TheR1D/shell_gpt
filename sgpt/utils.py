import os
from tempfile import NamedTemporaryFile

import typer

from click import BadParameter
from sgpt import OpenAIClient


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


def echo_chat_messages(chat_id: str) -> None:
    # Prints all messages from a specified chat ID to the console.
    for index, message in enumerate(OpenAIClient.chat_cache.show(chat_id)):
        color = "cyan" if index % 2 == 0 else "green"
        typer.secho(message, fg=color)


def echo_chat_ids() -> None:
    # Prints all existing chat IDs to the console.
    for chat_id in OpenAIClient.chat_cache.list():
        typer.echo(chat_id)
