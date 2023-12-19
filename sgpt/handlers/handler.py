from typing import Any, Dict, Generator, List

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from ..client import OpenAIClient
from ..config import cfg
from ..role import SystemRole


class Handler:
    def __init__(self, role: SystemRole) -> None:
        self.client = OpenAIClient(
            cfg.get("OPENAI_API_HOST"), cfg.get("OPENAI_API_KEY")
        )
        self.role = role
        self.disable_stream = cfg.get("DISABLE_STREAMING") == "false"
        self.color = cfg.get("DEFAULT_COLOR")
        self.theme_name = cfg.get("CODE_THEME")

    def _handle_with_markdown(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(prompt.strip())
        full_completion = ""
        with Live(
            Markdown(markup="", code_theme=self.theme_name),
            console=Console(),
            refresh_per_second=8,
        ) as live:
            if not self.disable_stream:
                live.update(
                    Markdown(markup="Loading...\r", code_theme=self.theme_name),
                    refresh=True,
                )
            for word in self.get_completion(messages=messages, **kwargs):
                full_completion += word
                live.update(
                    Markdown(full_completion, code_theme=self.theme_name),
                    refresh=not self.disable_stream,
                )
        return full_completion

    def _handle_with_plain_text(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(prompt.strip())
        full_completion = ""
        if not self.disable_stream:
            typer.echo("Loading...\r", nl=False)
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        # Overwrite "loading..."
        typer.echo("\033[K" if not self.disable_stream else "")
        return full_completion

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        yield from self.client.get_completion(**kwargs)

    def handle(self, prompt: str, **kwargs: Any) -> str:
        if self.role.name == "ShellGPT" or self.role.name == "Shell Command Descriptor":
            return self._handle_with_markdown(prompt, **kwargs)
        return self._handle_with_plain_text(prompt, **kwargs)
