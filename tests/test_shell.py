import os
from pathlib import Path
from unittest.mock import patch

import pytest

from sgpt.config import cfg
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, comp_args, mock_comp, runner


@patch("sgpt.handlers.handler.completion")
def test_shell(completion):
    role = SystemRole.get(DefaultRoles.SHELL.value)
    completion.return_value = mock_comp("git commit -m test")

    args = {"prompt": "make a commit using git", "--shell": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "git commit" in result.stdout
    assert "[E]xecute, [D]escribe, [A]bort:" in result.stdout


@patch("sgpt.handlers.handler.completion")
@pytest.mark.parametrize(
    "prefix,suffix",
    [
        ("", ""),
        ("some text before\n```powershell\n", "\n```" ""),
        ("```powershell\n", "\n```\nsome text after" ""),
        ("some text before\n```powershell\n", "\n```\nsome text after" ""),
        (
            "some text with ``` before\n```powershell\n",
            "\n```\nsome text with ``` after" "",
        ),
        ("```powershell\n", "\n```" ""),
        ("```\n", "\n```" ""),
        ("```powershell\r\n", "\r\n```" ""),
        ("```\r\n", "\r\n```" ""),
        ("```powershell\r", "\r```" ""),
        ("```\r", "\r```" ""),
    ],
)
@pytest.mark.parametrize("group_by_size", range(10))
def test_shell_no_backticks(completion, prefix: str, suffix: str, group_by_size: int):
    expected_output = "Get-Process | \nWhere-Object { $_.Port -eq 9000 }\r\n | Select-Object Id | Text \r\nwith '```' inside"
    produced_output = prefix + expected_output + suffix
    if group_by_size == 0:
        produced_tokens = list(produced_output)
    else:
        produced_tokens = [
            produced_output[i : i + group_by_size]
            for i in range(0, len(produced_output), group_by_size)
        ]
    assert produced_output == "".join(produced_tokens)

    role = SystemRole.get(DefaultRoles.SHELL.value)
    completion.return_value = mock_comp(produced_tokens)

    args = {"prompt": "find pid by port 9000", "--shell": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    index = result.stdout.find(expected_output)
    assert index >= 0
    rest = result.stdout[index + len(expected_output) :].strip()
    assert "`" not in rest
    assert result.exit_code == 0
    assert "[E]xecute, [D]escribe, [A]bort:" == rest


@patch("sgpt.printer.TextPrinter.live_print")
@patch("sgpt.printer.MarkdownPrinter.live_print")
@patch("sgpt.handlers.handler.completion")
def test_shell_no_markdown(completion, markdown_printer, text_printer):
    completion.return_value = mock_comp("git commit -m test")

    args = {"prompt": "make a commit using git", "--shell": True, "--md": True}
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    # Should ignore --md for --shell option and output text without markdown.
    markdown_printer.assert_not_called()
    text_printer.assert_called()


@patch("sgpt.handlers.handler.completion")
def test_shell_stdin(completion):
    completion.return_value = mock_comp("ls -l | sort")
    role = SystemRole.get(DefaultRoles.SHELL.value)

    args = {"prompt": "Sort by name", "--shell": True}
    stdin = "What is in current folder"
    result = runner.invoke(app, cmd_args(**args), input=stdin)

    expected_prompt = f"{stdin}\n\n{args['prompt']}"
    completion.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "ls -l | sort" in result.stdout
    assert "[E]xecute, [D]escribe, [A]bort:" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_describe_shell(completion):
    completion.return_value = mock_comp("lists the contents of a folder")
    role = SystemRole.get(DefaultRoles.DESCRIBE_SHELL.value)

    args = {"prompt": "ls", "--describe-shell": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "lists" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_describe_shell_stdin(completion):
    completion.return_value = mock_comp("lists the contents of a folder")
    role = SystemRole.get(DefaultRoles.DESCRIBE_SHELL.value)

    args = {"--describe-shell": True}
    stdin = "What is in current folder"
    result = runner.invoke(app, cmd_args(**args), input=stdin)

    expected_prompt = f"{stdin}"
    completion.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "lists" in result.stdout


@patch("os.system")
@patch("sgpt.handlers.handler.completion")
def test_shell_run_description(completion, system):
    completion.side_effect = [mock_comp("echo hello"), mock_comp("prints hello")]
    args = {"prompt": "echo hello", "--shell": True}
    inputs = "__sgpt__eof__\nd\ne\n"
    result = runner.invoke(app, cmd_args(**args), input=inputs)
    shell = os.environ.get("SHELL", "/bin/sh")
    system.assert_called_once_with(f"{shell} -c 'echo hello'")
    assert result.exit_code == 0
    assert "echo hello" in result.stdout
    assert "prints hello" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_shell_chat(completion):
    completion.side_effect = [mock_comp("ls"), mock_comp("ls | sort")]
    role = SystemRole.get(DefaultRoles.SHELL.value)
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "list folder", "--shell": True, "--chat": chat_name}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "ls" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "sort by name"
    result = runner.invoke(app, cmd_args(**args))
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
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    args["--code"] = True
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 2
    assert "Error" in result.stdout
    chat_path.unlink()
    # TODO: Shell chat can be recalled without --shell option.


@patch("os.system")
@patch("sgpt.handlers.handler.completion")
def test_shell_repl(completion, mock_system):
    completion.side_effect = [mock_comp("ls"), mock_comp("ls | sort")]
    role = SystemRole.get(DefaultRoles.SHELL.value)
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name, "--shell": True}
    inputs = ["__sgpt__eof__", "list folder", "sort by name", "e", "exit()"]
    result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
    shell = os.environ.get("SHELL", "/bin/sh")
    mock_system.assert_called_once_with(f"{shell} -c 'ls | sort'")

    expected_messages = [
        {"role": "system", "content": role.role},
        {"role": "user", "content": "list folder"},
        {"role": "assistant", "content": "ls"},
        {"role": "user", "content": "sort by name"},
        {"role": "assistant", "content": "ls | sort"},
    ]
    expected_args = comp_args(role, "", messages=expected_messages)
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    assert result.exit_code == 0
    assert ">>> list folder" in result.stdout
    assert "ls" in result.stdout
    assert ">>> sort by name" in result.stdout
    assert "ls | sort" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_shell_and_describe_shell(completion):
    args = {"prompt": "ls", "--describe-shell": True, "--shell": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_not_called()
    assert result.exit_code == 2
    assert "Error" in result.stdout


@patch("sgpt.handlers.handler.completion")
def test_shell_no_interaction(completion):
    completion.return_value = mock_comp("git commit -m test")
    role = SystemRole.get(DefaultRoles.SHELL.value)

    args = {
        "prompt": "make a commit using git",
        "--shell": True,
        "--no-interaction": True,
    }
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "git commit" in result.stdout
    assert "[E]xecute" not in result.stdout
