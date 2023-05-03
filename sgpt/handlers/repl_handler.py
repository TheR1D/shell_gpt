from typing import Any

import typer
from rich import print as rich_print
from rich.rule import Rule

from ..client import OpenAIClient
from ..role import DefaultRoles, SystemRole
from ..utils import run_command
from .chat_handler import ChatHandler


class ReplHandler(ChatHandler):
    def __init__(self, client: OpenAIClient, chat_id: str, role: SystemRole) -> None:
        super().__init__(client, chat_id, role)

    def handle(self, prompt: str, **kwargs: Any) -> None:  # type: ignore
        if self.initiated:
            rich_print(Rule(title="Chat History", style="bold magenta"))
            self.show_messages(self.chat_id)
            rich_print(Rule(style="bold magenta"))

        info_message = (
            "Entering REPL mode, press Ctrl+C to exit."
            if not self.role.name == DefaultRoles.SHELL.value
            else "Entering shell REPL mode, type [e] to execute commands or press Ctrl+C to exit."
        )
        typer.secho(info_message, fg="yellow")

        if not prompt:
            prompt = typer.prompt(">>>", prompt_suffix=" ")
        else:
            typer.echo(f">>> {prompt}")

        while True:
            full_completion = super().handle(prompt, **kwargs)
            prompt = typer.prompt(">>>", prompt_suffix=" ")
            if prompt == "exit()":
                # This is also useful during tests.
                raise typer.Exit()
            if self.role.name == DefaultRoles.SHELL.value:
                if prompt == "e":
                    typer.echo()
                    run_command(full_completion)
                    typer.echo()
                    rich_print(Rule(style="bold magenta"))
                    prompt = typer.prompt(">>> ", prompt_suffix=" ")
