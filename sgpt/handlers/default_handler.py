from pathlib import Path

from sgpt import OpenAIClient, cfg, make_prompt
from sgpt.utils import CompletionModes

from .handler import Handler

CHAT_CACHE_LENGTH = int(cfg.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(cfg.get("CHAT_CACHE_PATH"))


class DefaultHandler(Handler):
    def __init__(
        self,
        client: OpenAIClient,
        shell: bool = False,
        code: bool = False,
        model: str = "gpt-3.5-turbo",
    ) -> None:
        super().__init__(client)
        self.client = client
        self.mode = CompletionModes.get_mode(shell, code)
        self.model = model

    def make_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        return make_prompt.initial(
            prompt,
            self.mode == CompletionModes.SHELL,
            self.mode == CompletionModes.CODE,
        )
