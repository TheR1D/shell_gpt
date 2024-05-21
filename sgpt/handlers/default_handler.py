from pathlib import Path
from typing import Dict, List

from ..config import cfg
from ..role import SystemRole
from .handler import Handler

CHAT_CACHE_LENGTH = int(cfg.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(cfg.get("CHAT_CACHE_PATH"))
FORCE_USER_ROLE = cfg.get("FORCE_USER_ROLE") == "true"

class DefaultHandler(Handler):
    def __init__(self, role: SystemRole, markdown: bool) -> None:
        super().__init__(role, markdown)
        self.role = role

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        role = "system" if FORCE_USER_ROLE == False else "user"
        messages = [
            {"role": role, "content": self.role.role},
            {"role": "user", "content": prompt},
        ]
        return messages
