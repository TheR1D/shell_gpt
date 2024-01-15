from pathlib import Path
from unittest.mock import patch

from sgpt.config import cfg
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, comp_args, comp_chunks, make_args, parametrize, runner


@parametrize("completion", ["git commit -m test"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_shell(mock, completion):
    role = SystemRole.get(DefaultRoles.SHELL.value)
    mock.return_value = completion

    args = {"prompt": "make a commit using git", "--shell": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "git commit" in result.stdout
    assert "[E]xecute, [D]escribe, [A]bort:" in result.stdout


@parametrize("completion", ["ls -l | sort"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_shell_stdin(mock, completion):
    role = SystemRole.get(DefaultRoles.SHELL.value)
    mock.return_value = completion

    args = {"prompt": "Sort by name", "--shell": True}
    stdin = "What is in current folder"
    result = runner.invoke(app, make_args(**args), input=stdin)

    expected_prompt = f"{stdin}\n\n{args['prompt']}"
    mock.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "ls -l | sort" in result.stdout
    assert "[E]xecute, [D]escribe, [A]bort:" in result.stdout


@parametrize("completion", ["lists the contents of a folder"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_describe_shell(mock, completion):
    role = SystemRole.get(DefaultRoles.DESCRIBE_SHELL.value)
    mock.return_value = completion

    args = {"prompt": "ls", "--describe-shell": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "lists" in result.stdout


@parametrize("completion", ["lists the contents of a folder"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_describe_shell_stdin(mock, completion):
    role = SystemRole.get(DefaultRoles.DESCRIBE_SHELL.value)
    mock.return_value = completion

    args = {"--describe-shell": True}
    stdin = "What is in current folder"
    result = runner.invoke(app, make_args(**args), input=stdin)

    expected_prompt = f"{stdin}"
    mock.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "lists" in result.stdout


@parametrize("completion", ["echo hello"], indirect=True)
@patch("openai.resources.chat.Completions.create")
def test_shell_run_description(mock, completion):
    mock.return_value = completion
    args = {"prompt": "echo hello", "--shell": True}
    result = runner.invoke(app, make_args(**args), input="d\n")
    # TODO: Doesn't input "d" automatically.
    assert result.exit_code == 0
    # assert "prints hello" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_shell_chat(mock):
    mock.side_effect = [comp_chunks("ls"), comp_chunks("ls | sort")]
    role = SystemRole.get(DefaultRoles.SHELL.value)
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "list folder", "--shell": True, "--chat": chat_name}
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 0
    assert "ls" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "sort by name"
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 0
    assert "ls | sort" in result.stdout

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "list folder"},
        {"role": "assistant", "content": "ls"},
        {"role": "user", "content": "sort by name"},
        {"role": "assistant", "content": "ls | sort"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    mock.assert_called_with(**expected_args)
    assert mock.call_count == 2

    args["--code"] = True
    result = runner.invoke(app, make_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout
    chat_path.unlink()
    # TODO: Shell chat can be recalled without --shell option.


@patch("os.system")
@patch("openai.resources.chat.Completions.create")
def test_shell_repl(mock_completion, mock_system):
    mock_completion.side_effect = [comp_chunks("ls"), comp_chunks("ls | sort")]
    role = SystemRole.get(DefaultRoles.SHELL.value)
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name, "--shell": True}
    inputs = ["list folder", "sort by name", "e", "exit()"]
    result = runner.invoke(app, make_args(**args), input="\n".join(inputs))
    mock_system.called_once()

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "list folder"},
        {"role": "assistant", "content": "ls"},
        {"role": "user", "content": "sort by name"},
        {"role": "assistant", "content": "ls | sort"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    mock_completion.assert_called_with(**expected_args)
    assert mock_completion.call_count == 2

    assert result.exit_code == 0
    assert ">>> list folder" in result.stdout
    assert "ls" in result.stdout
    assert ">>> sort by name" in result.stdout
    assert "ls | sort" in result.stdout


@patch("openai.resources.chat.Completions.create")
def test_shell_and_describe_shell(mock):
    args = {"prompt": "ls", "--describe-shell": True, "--shell": True}
    result = runner.invoke(app, make_args(**args))

    mock.assert_not_called()
    assert result.exit_code == 2
    assert "Error" in result.stdout
