from typing import List, Dict, Generator

import typer

from sgpt import OpenAIClient
from sgpt.role import SystemRole


class Handler:
    def __init__(self, client: OpenAIClient, role: str = None) -> None:
        self.client = client
        self.role = role

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

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        # TODO: Should be overridden in ChatHandler.
        messages = []
        if self.role:
            role = SystemRole.get(self.role)
            messages.append({"role": "system", "content": role.role})
        else:
            prompt = self.make_prompt(prompt)
        messages.append({"role": "user", "content": prompt})
        return messages

    def handle(self, prompt: str, **kwargs) -> str:
        messages = self.make_messages(prompt)
        print(messages)
        full_completion = ""
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg="magenta", bold=True, nl=False)
            full_completion += word
        typer.echo()
        return full_completion
