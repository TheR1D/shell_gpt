"""
This test module will execute real commands using shell.
This means it will call sgpt.py with command line arguments.
Make sure you have your API key in place ~/.cfg/shell_gpt/.sgptrc
or ENV variable OPENAI_API_KEY.
It is useful for quick tests, saves a bit time.
"""

import json
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import ANY, patch
from uuid import uuid4

import typer
from typer.testing import CliRunner

from sgpt.__version__ import __version__
from sgpt.app import main
from sgpt.config import cfg
from sgpt.handlers.handler import Handler
from sgpt.role import SystemRole

runner = CliRunner()
app = typer.Typer()
app.command()(main)


class TestShellGpt(TestCase):
    @classmethod
    def setUpClass(cls):
        # Response streaming should be enabled for these tests.
        assert cfg.get("DISABLE_STREAMING") == "false"
        # ShellGPT optimised and tested with gpt-4 turbo.
        assert cfg.get("DEFAULT_MODEL") == "gpt-4o"
        # Make sure we will not call any functions.
        assert cfg.get("OPENAI_USE_FUNCTIONS") == "false"

    @staticmethod
    def get_arguments(prompt, **kwargs):
        arguments = [prompt]
        for key, value in kwargs.items():
            arguments.append(key)
            if isinstance(value, bool):
                continue
            arguments.append(value)
        arguments.append("--no-cache")
        return arguments

    def test_default(self):
        dict_arguments = {
            "prompt": "What is the capital of the Czech Republic?",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "Prague" in result.output

    def test_shell(self):
        dict_arguments = {
            "prompt": "make a commit using git",
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "git commit" in result.output

    def test_describe_shell(self):
        dict_arguments = {
            "prompt": "ls",
            "--describe-shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "lists" in result.output.lower()

    def test_code(self):
        """
        This test will request from OpenAI API a python code to make CLI app,
        which will be written to a temp file, and then it will be executed
        in shell with two positional int arguments. As the output we are
        expecting the result of multiplying them.
        """
        dict_arguments = {
            "prompt": (
                "Create a command line application using Python that "
                "accepts two positional arguments "
                "and prints the result of multiplying them."
            ),
            "--code": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        print(result.output)
        # Since output will be slightly different, there is no way how to test it precisely.
        assert "print" in result.output
        assert "*" in result.output
        with NamedTemporaryFile("w+", delete=False) as file:
            try:
                compile(result.output, file.name, "exec")
            except SyntaxError:
                assert False, "The output is not valid Python code."  # noqa: B011
            file.seek(0)
            file.truncate()
            file.write(result.output)
            file_path = file.name
        number_a = number_b = 2
        # Execute output code in the shell with arguments.
        arguments = ["python", file.name, str(number_a), str(number_b)]
        script_output = subprocess.run(arguments, stdout=subprocess.PIPE, check=True)
        os.remove(file_path)
        assert script_output.stdout.decode().strip(), number_a * number_b

    def test_chat_default(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "Remember my favorite number: 6",
            "--chat": f"test_{chat_name}",
            "--no-cache": True,
        }
        runner.invoke(app, self.get_arguments(**dict_arguments))
        dict_arguments["prompt"] = "What is my favorite number + 2?"
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "8" in result.output
        dict_arguments["--shell"] = True
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 2
        dict_arguments["--code"] = True
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        # If we have default chat, we cannot use --code or --shell.
        assert result.exit_code == 2

    def test_chat_shell(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "Create nginx docker container, forward ports 80, "
            "mount current folder with index.html",
            "--chat": f"test_{chat_name}",
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "docker run" in result.output
        assert "-p 80:80" in result.output
        assert "nginx" in result.output
        dict_arguments["prompt"] = "Also forward port 443."
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "-p 80:80" in result.output
        assert "-p 443:443" in result.output
        dict_arguments["--code"] = True
        del dict_arguments["--shell"]
        assert "--shell" not in dict_arguments
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        # If we are using --code, we cannot use --shell.
        assert result.exit_code == 2

    def test_chat_describe_shell(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "git add",
            "--chat": f"test_{chat_name}",
            "--describe-shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "adds" in result.output.lower() or "stages" in result.output.lower()
        dict_arguments["prompt"] = "'-A'"
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "all" in result.output

    def test_chat_code(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "Using python request localhost:80.",
            "--chat": f"test_{chat_name}",
            "--code": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "localhost:80" in result.output
        dict_arguments["prompt"] = "Change port to 443."
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "localhost:443" in result.output
        del dict_arguments["--code"]
        assert "--code" not in dict_arguments
        dict_arguments["--shell"] = True
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        # If we have --code chat, we cannot use --shell.
        assert result.exit_code == 2

    def test_list_chat(self):
        result = runner.invoke(app, ["--list-chats"])
        assert result.exit_code == 0
        assert "test_" in result.output

    def test_show_chat(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "Remember my favorite number: 6",
            "--chat": f"test_{chat_name}",
        }
        runner.invoke(app, self.get_arguments(**dict_arguments))
        dict_arguments["prompt"] = "What is my favorite number + 2?"
        runner.invoke(app, self.get_arguments(**dict_arguments))
        result = runner.invoke(app, ["--show-chat", f"test_{chat_name}"])
        assert result.exit_code == 0
        assert "Remember my favorite number: 6" in result.output
        assert "What is my favorite number + 2?" in result.output
        assert "8" in result.output

    def test_validation_code_shell(self):
        dict_arguments = {
            "prompt": "What is the capital of the Czech Republic?",
            "--code": True,
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 2
        assert "Only one of --shell, --describe-shell, and --code" in result.output

    def test_repl_default(
        self,
    ):
        dict_arguments = {
            "prompt": "",
            "--repl": "temp",
        }
        inputs = [
            "Please remember my favorite number: 6",
            "What is my favorite number + 2?",
            "exit()",
        ]
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )
        assert result.exit_code == 0
        assert ">>> Please remember my favorite number: 6" in result.output
        assert ">>> What is my favorite number + 2?" in result.output
        assert "8" in result.output

    def test_repl_multiline(
        self,
    ):
        dict_arguments = {
            "prompt": "",
            "--repl": "temp",
        }
        inputs = [
            '"""',
            "Please remember my favorite number: 6",
            "What is my favorite number + 2?",
            '"""',
            "exit()",
        ]
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )

        assert result.exit_code == 0
        assert '"""' in result.output
        assert "Please remember my favorite number: 6" in result.output
        assert "What is my favorite number + 2?" in result.output
        assert '"""' in result.output
        assert "8" in result.output

    def test_repl_shell(self):
        # Temp chat session from previous test should be overwritten.
        dict_arguments = {
            "prompt": "",
            "--repl": "temp",
            "--shell": True,
        }
        inputs = ["What is in current folder?", "Simple sort by name", "exit()"]
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )
        assert result.exit_code == 0
        assert "type [e] to execute commands" in result.output
        assert ">>> What is in current folder?" in result.output
        assert ">>> Simple sort by name" in result.output
        assert "ls -la" in result.output
        assert "sort" in result.output
        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / "temp"
        chat_messages = json.loads(tmp_chat.read_text())
        # TODO: Implement same check in chat mode tests.
        assert chat_messages[0]["content"].startswith("You are Shell Command Generator")
        assert chat_messages[0]["role"] == "system"
        assert chat_messages[1]["content"].startswith("What is in current folder?")
        assert chat_messages[1]["role"] == "user"
        assert chat_messages[2]["content"] == "ls -la"
        assert chat_messages[2]["role"] == "assistant"
        assert chat_messages[3]["content"] == "Simple sort by name"
        assert chat_messages[3]["role"] == "user"
        assert "sort" in chat_messages[4]["content"]
        assert chat_messages[4]["role"] == "assistant"

    def test_repl_describe_command(self):
        # Temp chat session from previous test should be overwritten.
        dict_arguments = {
            "prompt": "",
            "--repl": "temp",
            "--describe-shell": True,
        }
        inputs = ["pacman -S", "-yu", "exit()"]
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )
        assert result.exit_code == 0
        assert "install" in result.output.lower()
        assert "upgrade" in result.output.lower()

        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / "temp"
        chat_messages = json.loads(tmp_chat.read_text())
        assert chat_messages[0]["content"].startswith(
            "You are Shell Command Descriptor"
        )

    def test_repl_code(self):
        dict_arguments = {
            "prompt": "",
            "--repl": f"test_{uuid4()}",
            "--code": True,
        }
        inputs = (
            "Using python make request to localhost:8080",
            "Change port to 443",
            "exit()",
        )
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )
        assert result.exit_code == 0
        assert f">>> {inputs[0]}" in result.output
        assert "requests.get" in result.output
        assert "localhost:8080" in result.output
        assert f">>> {inputs[1]}" in result.output
        assert "localhost:443" in result.output

        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / dict_arguments["--repl"]
        chat_messages = json.loads(tmp_chat.read_text())
        assert chat_messages[0]["content"].startswith("You are Code Generator")
        assert chat_messages[0]["role"] == "system"

        # Coming back after exit.
        new_inputs = ("Change port to 80", "exit()")
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(new_inputs)
        )
        # Should include previous chat history.
        assert "Chat History" in result.output
        assert f"user: {inputs[1]}" in result.output

    def test_zsh_command(self):
        """
        The goal of this test is to verify that $SHELL
        specific commands are working as expected.
        In this case testing zsh specific "print" function.
        """
        if os.getenv("SHELL", "") != "/bin/zsh":
            return
        dict_arguments = {
            "prompt": 'Using zsh specific "print" function say hello world',
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input="y\n")
        stdout = result.output.strip()
        print(stdout)
        # TODO: Fix this test.
        # Not sure how os.system pipes the output to stdout,
        # but it is not part of the result.output.
        # assert "command not found" not in result.output
        # assert "hello world" in stdout.split("\n")[-1]

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_model_option(self, mocked_get_completion):
        dict_arguments = {
            "prompt": "What is the capital of the Czech Republic?",
            "--model": "gpt-4",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        mocked_get_completion.assert_called_once_with(
            messages=ANY,
            model="gpt-4",
            temperature=0.0,
            top_p=1.0,
            caching=False,
            functions=None,
        )
        assert result.exit_code == 0

    def test_color_output(self):
        color = cfg.get("DEFAULT_COLOR")
        role = SystemRole.get("ShellGPT")
        handler = Handler(role=role)
        assert handler.color == color
        os.environ["DEFAULT_COLOR"] = "red"
        handler = Handler(role=role)
        assert handler.color == "red"

    def test_simple_stdin(self):
        result = runner.invoke(app, input="What is the capital of Germany?\n")
        assert "Berlin" in result.output

    def test_shell_stdin_with_prompt(self):
        dict_arguments = {
            "prompt": "Sort by name",
            "--shell": True,
        }
        stdin = "What is in current folder\n"
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=stdin)
        assert "ls" in result.output
        assert "sort" in result.output

    def test_role(self):
        test_role = Path(cfg.get("ROLE_STORAGE_PATH")) / "json_generator.json"
        test_role.unlink(missing_ok=True)
        dict_arguments = {
            "prompt": "test",
            "--create-role": "json_generator",
        }
        input = (
            "Provide only valid plain JSON as response with valid field values. "
            + "Do not include any markdown formatting such as ```.\n"
        )
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=input)
        assert result.exit_code == 0

        dict_arguments = {
            "prompt": "test",
            "--list-roles": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "json_generator" in result.output

        dict_arguments = {
            "prompt": "test",
            "--show-role": "json_generator",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "You are json_generator" in result.output

        # Test with command line argument prompt.
        dict_arguments = {
            "prompt": "random username, password, email",
            "--role": "json_generator",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        generated_json = json.loads(result.output)
        assert "username" in generated_json
        assert "password" in generated_json
        assert "email" in generated_json

        # Test with stdin prompt.
        dict_arguments = {
            "prompt": "",
            "--role": "json_generator",
        }
        stdin = "random username, password, email"
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=stdin)
        assert result.exit_code == 0
        generated_json = json.loads(result.output)
        assert "username" in generated_json
        assert "password" in generated_json
        assert "email" in generated_json
        test_role.unlink(missing_ok=True)

    def test_shell_command_run_description(self):
        dict_arguments = {
            "prompt": "say hello",
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input="d\n")
        assert result.exit_code == 0
        # Can't really test it since stdin in disable for --shell flag.
        # for word in ("prints", "hello", "console"):
        #     assert word in result.output

    def test_version(self):
        dict_arguments = {
            "prompt": "",
            "--version": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input="d\n")
        assert __version__ in result.output

    # TODO: Implement function call tests.
