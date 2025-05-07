from typing import Any

import typer
from rich import print as rich_print
from rich.rule import Rule

from ..role import DefaultRoles, SystemRole
from ..utils import run_command, get_fixed_prompt, extract_command_from_completion
from .chat_handler import ChatHandler
from .default_handler import DefaultHandler


class ReplHandler(ChatHandler):
    def __init__(self, chat_id: str, role: SystemRole, markdown: bool) -> None:
        super().__init__(chat_id, role, markdown)

    @classmethod
    def _get_multiline_input(cls) -> str:
        multiline_input = ""
        while (user_input := typer.prompt("...", prompt_suffix="")) != '"""':
            multiline_input += user_input + "\n"
        return multiline_input

    def handle(self, init_prompt: str, **kwargs: Any) -> None:  # type: ignore
        if self.initiated:
            rich_print(Rule(title="Chat History", style="bold magenta"))
            self.show_messages(self.chat_id, self.markdown)
            rich_print(Rule(style="bold magenta"))

        info_message = (
            "Entering REPL mode, press Ctrl+C to exit."
            if not self.role.name == DefaultRoles.SHELL.value
            else (
                "Entering shell REPL mode, type [e] to execute commands "
                "or [d] to describe the commands, or [f] to fix the last command, press Ctrl+C to exit."
            )
        )
        typer.secho(info_message, fg="yellow")

        if init_prompt:
            rich_print(Rule(title="Input", style="bold purple"))
            typer.echo(init_prompt)
            rich_print(Rule(style="bold purple"))

        full_completion = ""
        while True:
            # Infinite loop until user exits with Ctrl+C.
            prompt = typer.prompt(">>>", prompt_suffix=" ")
            if prompt == '"""':
                prompt = self._get_multiline_input()
            if prompt == "exit()":
                raise typer.Exit()
            if init_prompt:
                prompt = f"{init_prompt}\n\n\n{prompt}"
                init_prompt = ""
            if self.role.name == DefaultRoles.SHELL.value and prompt == "f":
                prompt = get_fixed_prompt()
            command = extract_command_from_completion(full_completion)
            if self.role.name == DefaultRoles.SHELL.value and prompt == "e":
                typer.echo()
                run_command(command)
                typer.echo()
                rich_print(Rule(style="bold magenta"))
            elif self.role.name == DefaultRoles.SHELL.value and prompt == "d":
                DefaultHandler(
                    DefaultRoles.DESCRIBE_SHELL.get_role(), self.markdown
                ).handle(prompt=command, **kwargs)
            else:
                full_completion = super().handle(prompt=prompt, **kwargs)
