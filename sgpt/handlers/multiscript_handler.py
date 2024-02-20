from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import os
import glob

from ..cache import Cache
from ..config import cfg
from ..role import SystemRole

from ..handlers.handler import Handler
from ..utils import (

run_command,
list_scripts_with_content,
modify_or_create_scripts
)

class MultiScriptHandler:
    cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))

    def __init__(self, role: SystemRole) -> None:
        self.role = role

    def modify_or_create_scripts(self, modifications: List[Tuple[str, str]]):
        for filename, content in modifications:
            with open(filename, 'w') as file:
                file.write(content)
    
    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        messages = [
            {"role": "system", "content": self.role.role},
            {"role": "user", "content": prompt},
        ]
        return messages

    def handle(self,
        prompt: str,
        project_path: str,
        model: str,
        temperature: float,
        top_p: float,
        caching: bool,
        functions: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> None:
        import pdb
        pdb.set_trace()
        disable_stream = cfg.get("DISABLE_STREAMING") == "true"
        messages = self.make_messages(prompt.strip())
        generator = self.get_completion(
            model=model,
            temperature=temperature,
            top_p=top_p,
            messages=messages,
            functions=functions,
            caching=caching,
            **kwargs,
        )
        return self.printer(generator, not disable_stream)

