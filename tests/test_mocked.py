import json
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import ANY, patch
from uuid import uuid4
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from sgpt.__version__ import __version__
from sgpt.app import main
from sgpt.config import cfg
from sgpt.handlers.handler import Handler
from sgpt.role import SystemRole, DefaultRoles

import datetime
from unittest.mock import patch

from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDelta
from openai.types.chat.chat_completion_chunk import Choice as StreamChoice

runner = CliRunner()
app = typer.Typer()
app.command()(main)


@pytest.fixture
def stream_completion(request: Any):
    tokens_string = request.param
    return [
        ChatCompletionChunk(
            id="foo",
            model="gpt-4-1106-preview",
            object="chat.completion.chunk",
            choices=[
                StreamChoice(
                    index=0,
                    finish_reason=None,
                    delta=ChoiceDelta(content=token, role="assistant"),
                ),
            ],
            created=int(datetime.datetime.now().timestamp()),
        ) for token in tokens_string
    ]

def make_arguments(prompt, **kwargs):
    arguments = [prompt]
    for key, value in kwargs.items():
        arguments.append(key)
        if isinstance(value, bool):
            continue
        arguments.append(value)
    arguments.append("--no-cache")
    return arguments

@pytest.mark.parametrize("stream_completion", ["Prague"], indirect=True)
def test_default(stream_completion):
    with patch("openai.resources.chat.Completions.create") as mocked_stream:
        mocked_stream.return_value = stream_completion

        dict_arguments = {"prompt": "What is the capital of the Czech Republic?"}
        result = runner.invoke(app, make_arguments(**dict_arguments))

        mocked_stream.assert_called_once()
        print(mocked_stream.call_args)
        system_message = mocked_stream.call_args["kwargs"]["messages"][0]
        user_message = mocked_stream.call_args["kwargs"]["messages"][1]
        model = mocked_stream.call_args["kwargs"]["model"]
        temperature = mocked_stream.call_args["kwargs"]["temperature"]
        top_p = mocked_stream.call_args["kwargs"]["top_p"]
        functions = mocked_stream.call_args["kwargs"]["functions"]
        stream = mocked_stream.call_args["kwargs"]["stream"]

        expected_role = SystemRole.get(DefaultRoles.DEFAULT.value)
        print(expected_role)

        assert result.exit_code == 0
        assert "Prague" in result.stdout
        assert system_message["role"] == "system"
        assert system_message["content"] == expected_role.role
        assert user_message["role"] == "user"
        assert user_message["content"] == dict_arguments["prompt"]
