from typing import Any, Dict, List, Generator
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
        self.color = cfg.get("DEFAULT_COLOR")
        self.theme = cfg.get("CODE_THEME")
        self.console = Console()

    def make_prompt(self, prompt: str) -> str:
        raise NotImplementedError

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        yield from self.client.get_completion(**kwargs)

    def handle(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(self.make_prompt(prompt))
        full_completion = ""
        with Live(Markdown('', code_theme=self.theme), console=self.console) as live:
            for word in self.get_completion(messages=messages, **kwargs):
                full_completion += word
                live.update(Markdown(full_completion, code_theme=self.theme), refresh=True)
        return full_completion