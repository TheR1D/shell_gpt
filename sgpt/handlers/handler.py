from typing import Any, Dict, Generator, List

import typer

from ..client import OpenAIClient
from ..config import cfg


class Handler:
    def __init__(self, client: OpenAIClient) -> None:
        self.client = client
        self.color = cfg.get("DEFAULT_COLOR")

    def make_prompt(self, prompt: str) -> str:
        raise NotImplementedError

    def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
        caching: bool = True,
    ) -> Generator[str, None, None]:
        yield from self.client.get_completion(
            messages,
            model,
            temperature,
            top_probability,
            caching=caching,
        )

    def handle(self, prompt: str, **kwargs: Any) -> str:
        prompt = self.make_prompt(prompt)
        # print(prompt)
        # print(kwargs)
        messages = [{"role": "user", "content": prompt}]
        full_completion = ""
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        typer.echo()
        return full_completion
