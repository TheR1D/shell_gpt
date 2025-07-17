import os
import platform
import shlex
from tempfile import NamedTemporaryFile
from typing import Any, Callable
import shutil

import typer
from click import BadParameter, UsageError, Context

from sgpt.__version__ import __version__
from sgpt.config import cfg
from sgpt.integration import bash_integration, zsh_integration


def list_models(value: bool) -> None:
    """
    List all available models from litellm.
    """
    if not value:
        return
    # Litellm models are dynamically generated, so we need to import it here.
    from litellm import model_list  # type: ignore

    provider = cfg.get("LLM_API_PROVIDER")
    typer.echo(f"Available models for {provider}:")
    for model in model_list:
        if provider in model:
            typer.echo(f" - {model}")
    raise typer.Exit()


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


def option_callback(func: Callable) -> Callable:  # type: ignore
    def wrapper(cls: Any, value: str) -> None:
        if not value:
            return
        func(cls, value)
        raise typer.Exit()

    return wrapper


@option_callback
def install_shell_completion(ctx: Context, value: bool) -> None:
    """
    Install shell completion files for the specified shell.
    Currently only supports ZSH.
    """
    if not value:
        return

    shell = os.getenv("SHELL", "")
    if not shell.endswith('zsh'):
        typer.echo("Shell-GPT completions only available for ZSH.")
        return
    install_zsh_completion()


ZSH_COMPLETION_CONFIG = """
# Shell-GPT completions
fpath=(~/.zsh/completions $fpath)
autoload -U compinit
compinit -C
"""


def get_zsh_completion_file() -> str:
    """
    Returns the path to the ZSH completion file using importlib.resources
    """
    from importlib.resources import files
    completion_file = files('sgpt').joinpath('completions/_sgpt')
    if not completion_file.exists():
        raise FileNotFoundError('Completion file not found')
    return str(completion_file)


def install_zsh_completion() -> None:
    typer.echo("Installing ZSH completion...")
    completion_dir = os.path.expanduser("~/.zsh/completions")
    os.makedirs(completion_dir, exist_ok=True)

    try:
        completion_file = get_zsh_completion_file()
    except Exception as e:
        typer.echo(f"Error: Could not find completion file. Please reinstall the package. Details: {str(e)}")
        return

    try:
        shutil.copy(completion_file, os.path.join(completion_dir, "_sgpt"))
    except OSError as e:
        typer.echo(f"Error copying completion file: {e}")
        return
    else:
        typer.echo(f"Copied completion file to {completion_dir}/_sgpt")

    # Add the configuration to .zshrc
    zshrc_path = os.path.expanduser("~/.zshrc")
    with open(zshrc_path, "r", encoding="utf-8") as file:
        content = file.read()
    # Only add if it doesn't exist already
    if "Shell-GPT completions" not in content:
        with open(zshrc_path, "a", encoding="utf-8") as file:
            file.write(ZSH_COMPLETION_CONFIG)
        typer.echo(f"Updated {zshrc_path}")
    else:
        typer.echo("Shell-GPT completions already installed in .zshrc")


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
    if shell.endswith('zsh'):
        typer.echo("Installing ZSH integration...")

        zshrc_path = os.path.expanduser("~/.zshrc")
        with open(zshrc_path, "r", encoding="utf-8") as file:
            content = file.read()
        if "Shell-GPT integration ZSH" not in content:
            with open(zshrc_path, "a", encoding="utf-8") as file:
                file.write(zsh_integration)
            typer.echo(f"Updated {zshrc_path}")
        else:
            typer.echo("Shell-GPT integration already installed in .zshrc")

    elif "bash" in shell:
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
