from typing import Any, Dict, Generator, List

import typer

from ..client import OpenAIClient
from ..config import cfg
from ..role import SystemRole


class Handler:
    def __init__(self, role: SystemRole) -> None:
        self.client = OpenAIClient(
            cfg.get("OPENAI_API_HOST"), cfg.get("OPENAI_API_KEY")
        )
        self.role = role
        self.color = cfg.get("DEFAULT_COLOR")

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        yield from self.client.get_completion(**kwargs)

    def handle(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(prompt.strip())
        full_completion = ""
        stream = cfg.get("DISABLE_STREAMING") == "false"
        if not stream:
            typer.echo("Loading...\r", nl=False)
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        typer.echo("\033[K" if not stream else "")  # Overwrite "loading..."
        return full_completion
