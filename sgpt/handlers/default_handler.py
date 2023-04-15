from pathlib import Path

from ..client import OpenAIClient
from ..config import cfg
from ..role import SystemRole
from .handler import Handler

CHAT_CACHE_LENGTH = int(cfg.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(cfg.get("CHAT_CACHE_PATH"))


class DefaultHandler(Handler):
    def __init__(
        self,
        client: OpenAIClient,
        role: SystemRole,
        model: str = "gpt-3.5-turbo",
    ) -> None:
        super().__init__(client)
        self.client = client
        self.role = role
        self.model = model

    def make_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        return self.role.make_prompt(prompt, initial=True)
