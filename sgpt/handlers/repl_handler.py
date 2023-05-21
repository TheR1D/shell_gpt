from typing import Any

import typer
from rich import print as rich_print
from rich.rule import Rule

from ..role import DefaultRoles, SystemRole
from ..utils import run_command
from .chat_handler import ChatHandler
from .default_handler import DefaultHandler


class ReplHandler(ChatHandler):
    def __init__(self, chat_id: str, role: SystemRole) -> None:
        super().__init__(chat_id, role)

    def handle(self, prompt: str, **kwargs: Any) -> None:  # type: ignore
        if self.initiated:
            rich_print(Rule(title="Chat History", style="bold magenta"))
            self.show_messages(self.chat_id)
            rich_print(Rule(style="bold magenta"))

        info_message = (
            "Entering REPL mode, press Ctrl+C to exit."
            if not self.role.name == DefaultRoles.SHELL.value
            else (
                "Entering shell REPL mode, type [e] to execute commands "
                "or [d] to describe the commands, press Ctrl+C to exit."
            )
        )
        typer.secho(info_message, fg="yellow")

        full_completion = ""
        while True:
            # Infinite loop until user exits with Ctrl+C.
            prompt = typer.prompt(">>>", prompt_suffix=" ")
            if prompt == "exit()":
                # This is also useful during tests.
                raise typer.Exit()
            if self.role.name == DefaultRoles.SHELL.value and prompt == "e":
                typer.echo()
                run_command(full_completion)
                typer.echo()
                rich_print(Rule(style="bold magenta"))
            elif self.role.name == DefaultRoles.SHELL.value and prompt == "d":
                DefaultHandler(DefaultRoles.DESCRIBE_SHELL.get_role()).handle(
                    full_completion,
                    model=kwargs.get("model"),
                    temperature=kwargs.get("temperature"),
                    top_probability=kwargs.get("top_probability"),
                    caching=kwargs.get("caching"),
                )
            else:
                full_completion = super().handle(prompt, **kwargs)
