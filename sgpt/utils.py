import os
import platform
import shlex
from tempfile import NamedTemporaryFile
from typing import Any, Callable, List, Tuple

import typer
from click import BadParameter, UsageError

from sgpt.__version__ import __version__
from sgpt.integration import bash_integration, zsh_integration


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

def list_scripts_with_content(directory: str) -> List[Tuple[str, str]]:
    """
    List all Python scripts in the given directory with their content.

    :param directory: The directory to search for Python scripts.
    :return: A list of tuples containing the script name and its content.
    """
    script_extensions = (
         ".py",  # Python
         ".js",  # JavaScript
         ".java",  # Java
         ".rb",  # Ruby
         ".php",  # PHP
         ".cpp", ".cc", ".cxx", ".c++", ".c",  # C++
         ".cs",  # C#
         ".go",  # Go
         ".rs",  # Rust
         ".swift",  # Swift
         ".ts",  # TypeScript
         ".sh",  # Shell script
         # Add other extensions as needed
     )
    scripts = []
    for filename in os.listdir(directory):
        if filename.endswith(script_extensions):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                content = file.read()
            scripts.append((filename, content))
    return scripts

def parse_modifications(completion: str, script_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    modifications = []
    lines = completion.split('\n')
    current_file = None
    current_content = []
    for line in lines:
        if line.startswith('File: '):
            if current_file is not None:
                modifications.append((current_file, '\n'.join(current_content)))
                current_content = []
            current_file = line[len('File: '):].strip()
        else:
            current_content.append(line)
    if current_file is not None:
        modifications.append((current_file, '\n'.join(current_content)))
    return modifications


def modify_or_create_scripts(modifications: List, directory: str) -> None:
    """
    Modify or create Python scripts based on the LLM output.

    :param llm_output: The output from the language model, which includes instructions
                       for modifying or creating scripts.
    :param directory: The directory where the scripts are to be modified or created.
    """
    # Apply the modifications or create new scripts
    for script in modifications:
        filename = script[0]
        content = script[1]
        filepath = os.path.join(directory, filename)

        # Write the new content to the file, creating it if it does not exist
        with open(filepath, 'w') as file:
            file.write(content)

def option_callback(func: Callable) -> Callable:  # type: ignore
    def wrapper(cls: Any, value: str) -> None:
        if not value:
            return
        func(cls, value)
        raise typer.Exit()

    return wrapper


@option_callback
def install_shell_integration(*_args: Any) -> None:
    """
    Installs shell integration. Currently only supports ZSH and Bash.
    Allows user to get shell completions in terminal by using hotkey.
    Replaces current "buffer" of the shell with the completion.
    """
    # TODO: Add support for Windows.
    # TODO: Implement updates.
    shell = os.getenv("SHELL", "")
    if shell == "/bin/zsh":
        typer.echo("Installing ZSH integration...")
        with open(os.path.expanduser("~/.zshrc"), "a", encoding="utf-8") as file:
            file.write(zsh_integration)
    elif shell == "/bin/bash":
        typer.echo("Installing Bash integration...")
        with open(os.path.expanduser("~/.bashrc"), "a", encoding="utf-8") as file:
            file.write(bash_integration)
    else:
        raise UsageError("ShellGPT integrations only available for ZSH and Bash.")

    typer.echo("Done! Restart your shell to apply changes.")


@option_callback
def get_sgpt_version(*_args: Any) -> None:
    """
    Displays the current installed version of ShellGPT
    """
    typer.echo(f"ShellGPT {__version__}")
