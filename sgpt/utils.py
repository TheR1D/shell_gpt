import os
import shlex

from enum import Enum
from tempfile import NamedTemporaryFile

import platform

from click import BadParameter


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


def run_command(command: str) -> None:
    """
    Runs a command in the user's shell.
    It is aware of the current user's $SHELL.
    :param command: A shell command to run.
    """
    if platform.system() == "Windows":
        is_powershell = len(os.getenv("PSModulePath", "").split(os.pathsep)) >= 3
        full_command = (
            f'powershell.exe -Command "{command}"'
            if is_powershell
            else f'cmd.exe /c "{command}"'
        )
    else:
        shell = os.environ.get("SHELL", "/bin/sh")
        full_command = f"{shell} -c {shlex.quote(command)}"

    os.system(full_command)
