import os

import typer

from rich import print as rich_print
from rich.rule import Rule

from sgpt.handlers.chat_handler import ChatHandler
from sgpt.client import OpenAIClient
from sgpt.utils import CompletionModes


class ReplHandler(ChatHandler):
    def __init__(  # pylint: disable=useless-parent-delegation,too-many-arguments
        self,
        client: OpenAIClient,
        chat_id: str,
        shell: bool = False,
        code: bool = False,
        model: str = "gpt-3.5-turbo",
    ):
        super().__init__(client, chat_id, shell, code, model)

    def handle(self, prompt: str, **kwargs) -> None:
        if self.initiated:
            rich_print(Rule(title="Chat History", style="bold magenta"))
            self.show_messages(self.chat_id)
            rich_print(Rule(style="bold magenta"))

        info_message = (
            "Entering REPL mode, press Ctrl+C to exit."
            if not self.mode == CompletionModes.SHELL
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
            if self.mode == CompletionModes.SHELL:
                if prompt == "e":
                    typer.echo()
                    os.system(full_completion)
                    typer.echo()
                    rich_print(Rule(style="bold magenta"))
                    prompt = typer.prompt(">>> ", prompt_suffix=" ")
