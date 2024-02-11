from pathlib import Path
from unittest.mock import patch

import typer
from typer.testing import CliRunner

from sgpt import config, main
from sgpt.__version__ import __version__
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, comp_args, mock_comp, runner

role = SystemRole.get(DefaultRoles.DEFAULT.value)
cfg = config.cfg


@patch("litellm.completion")
def test_default(completion):
    completion.return_value = mock_comp("Prague")

    args = {"prompt": "capital of the Czech Republic?"}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("litellm.completion")
def test_default_stdin(completion):
    completion.return_value = mock_comp("Prague")

    stdin = "capital of the Czech Republic?"
    result = runner.invoke(app, cmd_args(), input=stdin)

    completion.assert_called_once_with(**comp_args(role, stdin))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("rich.console.Console.print")
@patch("litellm.completion")
def test_show_chat_use_markdown(completion, console_print):
    completion.return_value = mock_comp("ok")
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "my number is 2", "--chat": chat_name}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert chat_path.exists()

    result = runner.invoke(app, ["--show-chat", chat_name])
    assert result.exit_code == 0
    console_print.assert_called()


@patch("rich.console.Console.print")
@patch("litellm.completion")
def test_show_chat_no_use_markdown(completion, console_print):
    completion.return_value = mock_comp("ok")
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    # Flag '--code' doesn't use markdown
    args = {"prompt": "my number is 2", "--chat": chat_name, "--code": True}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert chat_path.exists()

    result = runner.invoke(app, ["--show-chat", chat_name])
    assert result.exit_code == 0
    console_print.assert_not_called()


@patch("litellm.completion")
def test_default_chat(completion):
    completion.side_effect = [mock_comp("ok"), mock_comp("4")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "my number is 2", "--chat": chat_name}
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


@patch("litellm.completion")
def test_default_repl(completion):
    completion.side_effect = [mock_comp("ok"), mock_comp("8")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name}
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


@patch("litellm.completion")
def test_default_repl_stdin(completion):
    completion.side_effect = [mock_comp("ok init"), mock_comp("ok another")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    my_runner = CliRunner()
    my_app = typer.Typer()
    my_app.command()(main)

    args = {"--repl": chat_name}
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


@patch("litellm.completion")
def test_llm_options(completion):
    completion.return_value = mock_comp("Berlin")

    args = {
        "prompt": "capital of the Germany?",
        "--model": "gpt-4-test",
        "--temperature": 0.5,
        "--top-p": 0.5,
        "--no-functions": True,
    }
    result = runner.invoke(app, cmd_args(**args))

    expected_args = comp_args(
        role=role,
        prompt=args["prompt"],
        model=args["--model"],
        temperature=args["--temperature"],
        top_p=args["--top-p"],
        functions=None,
    )
    completion.assert_called_once_with(**expected_args)
    assert result.exit_code == 0
    assert "Berlin" in result.stdout


@patch("litellm.completion")
def test_version(completion):
    args = {"--version": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_not_called()
    assert __version__ in result.stdout
