from unittest.mock import ANY

import typer
from litellm import completion as completion
from typer.testing import CliRunner

from sgpt import main
from sgpt.config import cfg

runner = CliRunner()
app = typer.Typer()
app.command()(main)


def mock_comp(tokens_string):
    model = cfg.get("DEFAULT_MODEL")
    return completion(model=model, mock_response=tokens_string, stream=True)


def cmd_args(prompt="", **kwargs):
    arguments = [prompt]
    for key, value in kwargs.items():
        arguments.append(key)
        if isinstance(value, bool):
            continue
        arguments.append(value)
    arguments.append("--no-cache")
    arguments.append("--no-functions")
    return arguments


def comp_args(role, prompt, **kwargs):
    return {
        "messages": [
            {"role": "system", "content": role.role},
            {"role": "user", "content": prompt},
        ],
        "model": cfg.get("DEFAULT_MODEL"),
        "temperature": 0.0,
        "top_p": 1.0,
        "functions": None,
        "stream": True,
        "api_key": ANY,
        "base_url": ANY,
        "timeout": ANY,
        **kwargs,
    }
