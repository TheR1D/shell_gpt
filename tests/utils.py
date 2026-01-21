from datetime import datetime

import typer
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as StreamChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from typer.testing import CliRunner

from sgpt import main
from sgpt.config import cfg

runner = CliRunner()
app = typer.Typer()
app.command()(main)


def mock_comp(tokens_string):
    return [
        ChatCompletionChunk(
            id="foo",
            model=cfg.get("DEFAULT_MODEL"),
            object="chat.completion.chunk",
            choices=[
                StreamChoice(
                    index=0,
                    finish_reason=None,
                    delta=ChoiceDelta(content=token, role="assistant"),
                ),
            ],
            created=int(datetime.now().timestamp()),
        )
        for token in tokens_string
    ]


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
    model = kwargs.get("model", cfg.get("DEFAULT_MODEL"))

    # Mirror production logic: GPT-5 and o-series models require temperature 1.0,
    # while other models default to 0.0 in tests.
    if model.startswith("gpt-5") or model.startswith("o"):
        expected_temp = 1.0
    else:
        expected_temp = 0.0

    return {
        "messages": [
            {"role": "system", "content": role.role},
            {"role": "user", "content": prompt},
        ],
        "model": model,
        "temperature": expected_temp,
        "top_p": 1.0,
        "stream": True,
        **kwargs,
    }
