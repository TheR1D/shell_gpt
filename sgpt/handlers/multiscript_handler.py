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
modify_or_create_scripts,
parse_modifications
)

class MultiScriptHandler(Handler):
    cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))

    def __init__(self, role: SystemRole) -> None:
        self.role = role

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        messages = [
            {"role": "system", "content": self.role.role},
            {"role": "user", "content": prompt},
        ]
        return messages
    
    def handle(self,
            prompt: str,
            model: str,
            temperature: float,
            top_p: float,
            caching: bool,
            functions: Optional[List[Dict[str, str]]] = None,
            **kwargs: Any,
        ) -> str:
            project_path = kwargs.get('project_path', '')
            disable_stream = cfg.get("DISABLE_STREAMING") == "true"
            messages = self.make_messages(prompt.strip())

            # Add the list and content of each of the code scripts in the current folder tree to the prompt
            script_list = list_scripts_with_content(project_path)
            prompt_with_scripts = prompt + "\n\n" + "\n\n".join(
                f"File: {script[0]}\n\n{script[1]}" for script in script_list
            )
            messages[-1]["content"] = prompt_with_scripts
            generator = self.get_completion(
                model=model,
                temperature=temperature,
                top_p=top_p,
                messages=messages,
                functions=functions,
                caching=caching
            )
            completion = "".join(generator)
            modifications = parse_modifications(completion, script_list)

            # Apply the modifications to the scripts
            modify_or_create_scripts(modifications=modifications,directory=project_path)
            
            modified_scripts_message = "Scripts modified: "+"\n".join(list(modifications.keys())) 
            return modified_scripts_message
