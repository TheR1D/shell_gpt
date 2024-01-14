from pathlib import Path
from unittest.mock import patch

from sgpt.config import cfg
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, comp_args, comp_chunks, make_args, parametrize, runner

role = SystemRole.get(DefaultRoles.CODE.value)


@parametrize("completion", ["print('Hello World')"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_code_generation(mock, completion):
    mock.return_value = completion

    args = {"prompt": "hello world python", "--code": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "print('Hello World')" in result.stdout


@parametrize("completion", ["# Hello\nprint('Hello')"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_code_generation_stdin(mock, completion):
    mock.return_value = completion

    args = {"prompt": "make comments for code", "--code": True}
    stdin = "print('Hello')"
    result = runner.invoke(app, make_args(**args), input=stdin)

    expected_prompt = f"{stdin}\n\n{args['prompt']}"
    mock.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "# Hello" in result.stdout
    assert "print('Hello')" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_code_chat(mock):
    mock.side_effect = [
        comp_chunks("print('hello')"),
        comp_chunks("print('hello')\nprint('world')"),
    ]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "print hello", "--code": True, "--chat": chat_name}
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 0
    assert "print('hello')" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "also print world"
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 0
    assert "print('hello')" in result.stdout
    assert "print('world')" in result.stdout

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "print hello"},
        {"role": "assistant", "content": "print('hello')"},
        {"role": "user", "content": "also print world"},
        {"role": "assistant", "content": "print('hello')\nprint('world')"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    mock.assert_called_with(**expected_args)
    assert mock.call_count == 2

    args["--shell"] = True
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout
    chat_path.unlink()
    # TODO: Code chat can be recalled without --code option.


@patch("openai.resources.chat.Completions.create")
def test_code_repl(mock_completion):
    mock_completion.side_effect = [
        comp_chunks("print('hello')"),
        comp_chunks("print('hello')\nprint('world')"),
    ]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name, "--code": True}
    inputs = ["print hello", "also print world", "exit()"]
    result = runner.invoke(app, make_args(**args), input="\n".join(inputs))

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "print hello"},
        {"role": "assistant", "content": "print('hello')"},
        {"role": "user", "content": "also print world"},
        {"role": "assistant", "content": "print('hello')\nprint('world')"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    mock_completion.assert_called_with(**expected_args)
    assert mock_completion.call_count == 2

    assert result.exit_code == 0
    assert ">>> print hello" in result.stdout
    assert "print('hello')" in result.stdout
    assert ">>> also print world" in result.stdout
    assert "print('world')" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_code_and_shell(mock):
    args = {"--code": True, "--shell": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_not_called()
    assert result.exit_code == 2
    assert "Error" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_code_and_describe_shell(mock):
    args = {"--code": True, "--describe-shell": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_not_called()
    assert result.exit_code == 2
    assert "Error" in result.stdout
