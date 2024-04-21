from pathlib import Path
from unittest.mock import patch

import typer
from typer.testing import CliRunner

from sgpt import config, main
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, comp_args, mock_comp, runner

role = SystemRole.get(DefaultRoles.RAW.value)
cfg = config.cfg


@patch("sgpt.handlers.handler.completion")
def test_raw_long_option(completion):
    completion.return_value = mock_comp("Prague")

    args = {"prompt": "capital of the Czech Republic?", "--raw": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_raw_short_option(completion):
    completion.return_value = mock_comp("Prague")

    args = {"prompt": "capital of the Czech Republic?", "-r": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_raw_stdin(completion):
    completion.return_value = mock_comp("Prague")

    args = {"--raw": True}
    stdin = "capital of the Czech Republic?"
    result = runner.invoke(app, cmd_args(**args), input=stdin)

    completion.assert_called_once_with(**comp_args(role, stdin))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_raw_chat(completion):
    completion.side_effect = [mock_comp("ok"), mock_comp("4")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "my number is 2", "--raw": True, "--chat": chat_name}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "ok" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "my number + 2?"
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "4" in result.stdout

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "my number is 2"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "my number + 2?"},
        {"role": "assistant", "content": "4"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    result = runner.invoke(app, ["--list-chats"])
    assert result.exit_code == 0
    assert "_test" in result.stdout

    result = runner.invoke(app, ["--show-chat", chat_name])
    assert result.exit_code == 0
    assert "my number is 2" in result.stdout
    assert "ok" in result.stdout
    assert "my number + 2?" in result.stdout
    assert "4" in result.stdout

    args["--shell"] = True
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout

    args["--code"] = True
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout
    chat_path.unlink()


@patch("sgpt.handlers.handler.completion")
def test_raw_repl(completion):
    completion.side_effect = [mock_comp("ok"), mock_comp("8")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--raw": True, "--repl": chat_name}
    inputs = ["__sgpt__eof__", "my number is 6", "my number + 2?", "exit()"]
    result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "my number is 6"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "my number + 2?"},
        {"role": "assistant", "content": "8"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    assert result.exit_code == 0
    assert ">>> my number is 6" in result.stdout
    assert "ok" in result.stdout
    assert ">>> my number + 2?" in result.stdout
    assert "8" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_raw_repl_stdin(completion):
    completion.side_effect = [mock_comp("ok init"), mock_comp("ok another")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    my_runner = CliRunner()
    my_app = typer.Typer()
    my_app.command()(main)

    args = {"--raw": True, "--repl": chat_name}
    inputs = ["this is stdin", "__sgpt__eof__", "prompt", "another", "exit()"]
    result = my_runner.invoke(my_app, cmd_args(**args), input="\n".join(inputs))

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "this is stdin\n\n\n\nprompt"},
        {"role": "assistant", "content": "ok init"},
        {"role": "user", "content": "another"},
        {"role": "assistant", "content": "ok another"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    assert result.exit_code == 0
    assert "this is stdin" in result.stdout
    assert ">>> prompt" in result.stdout
    assert "ok init" in result.stdout
    assert ">>> another" in result.stdout
    assert "ok another" in result.stdout
