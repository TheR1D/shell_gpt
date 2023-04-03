from typing import List, Dict, Generator

import typer

from sgpt import OpenAIClient


class Handler:
    def __init__(self, client: OpenAIClient) -> None:
        self.client = client

    def make_prompt(self, prompt) -> str:
        raise NotImplementedError

    def get_completion(  # pylint: disable=too-many-arguments
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
        caching: bool = True,
    ) -> Generator:
        yield from self.client.get_completion(
            messages,
            model,
            temperature,
            top_probability,
            caching=caching,
        )

    def handle(self, prompt: str, **kwargs) -> str:
        prompt = self.make_prompt(prompt)
        messages = [{"role": "user", "content": prompt}]
        full_completion = ""
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg="magenta", bold=True, nl=False)
            full_completion += word
        typer.echo()
        return full_completion
