from typing import Any, Dict, Generator, List

import typer

from ..client import OpenAIClient
from ..config import cfg
from ..role import SystemRole


class Handler:
    def __init__(self, client: OpenAIClient, role: SystemRole) -> None:
        self.client = client
        self.role = role
        self.color = cfg.get("DEFAULT_COLOR")

    def make_prompt(self, prompt: str) -> str:
        raise NotImplementedError

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        yield from self.client.get_completion(**kwargs)

    def handle(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(self.make_prompt(prompt))
        full_completion = ""
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        typer.echo()
        return full_completion
