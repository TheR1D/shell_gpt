from pathlib import Path
from unittest.mock import patch

from sgpt import config
from sgpt.__version__ import __version__
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, comp_args, comp_chunks, make_args, parametrize, runner

role = SystemRole.get(DefaultRoles.DEFAULT.value)
cfg = config.cfg


@parametrize("completion", ["Prague"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_default(mock, completion):
    mock.return_value = completion

    args = {"prompt": "capital of the Czech Republic?"}
    result = runner.invoke(app, make_args(**args))

    mock.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@parametrize("completion", ["Prague"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_default_stdin(mock, completion):
    mock.return_value = completion

    stdin = "capital of the Czech Republic?"
    result = runner.invoke(app, make_args(), input=stdin)

    mock.assert_called_once_with(**comp_args(role, stdin))
    assert result.exit_code == 0
    assert "Prague" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_default_chat(mock):
    mock.side_effect = [comp_chunks("ok"), comp_chunks("4")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "my number is 2", "--chat": chat_name}
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 0
    assert "ok" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "my number + 2?"
    result = runner.invoke(app, make_args(**args))
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
    mock.assert_called_with(**expected_args)
    assert mock.call_count == 2

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
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout

    args["--code"] = True
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout
    chat_path.unlink()


@patch("openai.resources.chat.Completions.create")
def test_default_repl(mock):
    mock.side_effect = [comp_chunks("ok"), comp_chunks("8")]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name}
    inputs = ["my number is 6", "my number + 2?", "exit()"]
    result = runner.invoke(app, make_args(**args), input="\n".join(inputs))

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "my number is 6"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "my number + 2?"},
        {"role": "assistant", "content": "8"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    mock.assert_called_with(**expected_args)
    assert mock.call_count == 2

    assert result.exit_code == 0
    assert ">>> my number is 6" in result.stdout
    assert "ok" in result.stdout
    assert ">>> my number + 2?" in result.stdout
    assert "8" in result.stdout


@parametrize("completion", ["Berlin"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_llm_options(mock, completion):
    mock.return_value = completion

    args = {
        "prompt": "capital of the Germany?",
        "--model": "gpt-4-test",
        "--temperature": 0.5,
        "--top-p": 0.5,
        "--no-functions": True,
    }
    result = runner.invoke(app, make_args(**args))

    expected_args = comp_args(
        role=role,
        prompt=args["prompt"],
        model=args["--model"],
        temperature=args["--temperature"],
        top_p=args["--top-p"],
        functions=None,
    )
    mock.assert_called_once_with(**expected_args)
    assert result.exit_code == 0
    assert "Berlin" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_version(mock):
    args = {"--version": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_not_called()
    assert __version__ in result.stdout
