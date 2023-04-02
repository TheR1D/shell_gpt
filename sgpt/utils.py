import os
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import Callable

from click import BadParameter
import typer


class CompletionModes(Enum):
    NORMAL = "normal"
    SHELL = "shell"
    CODE = "code"

    @classmethod
    def get_mode(cls, shell, code) -> "CompletionModes":
        if shell:
            return CompletionModes.SHELL
        if code:
            return CompletionModes.CODE
        return CompletionModes.NORMAL


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
    with open(file_path, "r", encoding="utf-8") as file:
        output = file.read()
    os.remove(file_path)
    if not output:
        raise BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output


def option_callback(func: Callable) -> Callable:
    def wrapper(cls, value):
        if not value:
            return
        func(cls)
        raise typer.Exit()
    return wrapper
