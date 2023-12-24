from pathlib import Path
from typing import Any, Dict, Generator, List

import typer
from openai import OpenAI
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from ..cache import Cache
from ..config import cfg
from ..role import SystemRole

cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))


class Handler:
    def __init__(self, role: SystemRole) -> None:
        self.client = OpenAI(
            base_url=cfg.get("OPENAI_BASE_URL"),
            api_key=cfg.get("OPENAI_API_KEY"),
            timeout=int(cfg.get("REQUEST_TIMEOUT")),
        )
        self.role = role
        self.model = cfg.get("DEFAULT_MODEL")
        self.disable_stream = cfg.get("DISABLE_STREAMING") == "true"
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
            if self.disable_stream:
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
        if self.disable_stream:
            typer.echo("Loading...\r", nl=False)
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        # Overwrite "loading..."
        typer.echo("\033[K" if not self.disable_stream else "")
        return full_completion

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def create_prompt(self, prompt: str) -> List[Dict[str, Any]]:
        prompt_content = [{"type": "text", "text": prompt}]

        if self.image_url:
            prompt_content.append(
                {"type": "image_url", "image_url": {"url": self.image_url}}
            )
        return prompt_content

    @cache
    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        self.disable_stram = True
        if self.disable_stream:
            completion = self.client.chat.completions.create(**kwargs)
            yield completion.choices[0].message.content
            return

        for chunk in self.client.chat.completions.create(**kwargs, stream=True):
            yield from chunk.choices[0].delta.content or ""

    def handle(self, prompt: str, **kwargs: Any) -> str:
        if "image_url" in kwargs:
            self.image_url = kwargs.pop("image_url")
        if self.role.name == "ShellGPT" or self.role.name == "Shell Command Descriptor":
            return self._handle_with_markdown(prompt, **kwargs)
        return self._handle_with_plain_text(prompt, **kwargs)
