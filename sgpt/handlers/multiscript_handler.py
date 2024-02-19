from typing import List, Tuple
import os
import glob

from sgpt.handlers.default_handler import DefaultHandler
from sgpt.utils import (
run_command,
list_scripts_with_content,
modify_or_create_scripts
)

class MultiScriptHandler(Handler):
    def __init__(self, prompt: str, **kwargs):
        super().__init__(prompt, **kwargs)

    def modify_or_create_scripts(self, modifications: List[Tuple[str, str]]):
        for filename, content in modifications:
            with open(filename, 'w') as file:
                file.write(content)


    def handle(self):

