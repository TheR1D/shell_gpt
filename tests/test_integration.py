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
from time import sleep
from unittest import TestCase
from unittest.mock import ANY, patch
from uuid import uuid4

import typer
from typer.testing import CliRunner

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

    def setUp(self) -> None:
        # Just to not spam the API.
        sleep(1)

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
        assert "Prague" in result.stdout

    def test_shell(self):
        dict_arguments = {
            "prompt": "make a commit using git",
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "git commit" in result.stdout

    def test_describe_shell(self):
        dict_arguments = {
            "prompt": "ls",
            "--describe-shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "List " in result.stdout

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
        print(result.stdout)
        # Since output will be slightly different, there is no way how to test it precisely.
        assert "print" in result.stdout
        assert "*" in result.stdout
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
        assert "8" in result.stdout
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
        assert "docker run" in result.stdout
        assert "-p 80:80" in result.stdout
        assert "nginx" in result.stdout
        dict_arguments["prompt"] = "Also forward port 443."
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "-p 80:80" in result.stdout
        assert "-p 443:443" in result.stdout
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
        assert "Add file contents to the index." in result.stdout
        dict_arguments["prompt"] = "'-A'"
        # Prevent Too Many Requests.
        sleep(1)
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "all" in result.stdout

    def test_chat_code(self):
        chat_name = uuid4()
        dict_arguments = {
            "prompt": "Using python request localhost:80.",
            "--chat": f"test_{chat_name}",
            "--code": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "localhost:80" in result.stdout
        dict_arguments["prompt"] = "Change port to 443."
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "localhost:443" in result.stdout
        del dict_arguments["--code"]
        assert "--code" not in dict_arguments
        dict_arguments["--shell"] = True
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        # If we have --code chat, we cannot use --shell.
        assert result.exit_code == 2

    def test_list_chat(self):
        result = runner.invoke(app, ["--list-chats"])
        assert result.exit_code == 0
        assert "test_" in result.stdout

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
        assert "Remember my favorite number: 6" in result.stdout
        assert "What is my favorite number + 2?" in result.stdout
        assert "8" in result.stdout

    def test_validation_code_shell(self):
        dict_arguments = {
            "prompt": "What is the capital of the Czech Republic?",
            "--code": True,
            "--shell": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 2
        assert "Only one of --shell, --describe-shell, and --code" in result.stdout

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
        assert ">>> Please remember my favorite number: 6" in result.stdout
        assert ">>> What is my favorite number + 2?" in result.stdout
        assert "8" in result.stdout

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
        assert '"""' in result.stdout
        assert "Please remember my favorite number: 6" in result.stdout
        assert "What is my favorite number + 2?" in result.stdout
        assert '"""' in result.stdout
        assert "8" in result.stdout

    def test_repl_shell(self):
        # Temp chat session from previous test should be overwritten.
        dict_arguments = {
            "prompt": "",
            "--repl": "temp",
            "--shell": True,
        }
        inputs = ["What is in current folder?", "Sort by name", "exit()"]
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(inputs)
        )
        assert result.exit_code == 0
        assert "type [e] to execute commands" in result.stdout
        assert ">>> What is in current folder?" in result.stdout
        assert ">>> Sort by name" in result.stdout
        assert "ls" in result.stdout
        assert "ls | sort" in result.stdout
        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / "temp"
        chat_messages = json.loads(tmp_chat.read_text())
        # TODO: Implement same check in chat mode tests.
        assert chat_messages[0]["content"].startswith("###")
        assert chat_messages[0]["content"].endswith("\n###\nCommand:")
        assert chat_messages[1]["content"] == "ls"
        assert chat_messages[2]["content"].endswith("\nCommand:")
        assert chat_messages[3]["content"] == "ls | sort"

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
        assert "Install" in result.stdout
        assert "Update" in result.stdout

        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / "temp"
        chat_messages = json.loads(tmp_chat.read_text())
        assert chat_messages[0]["content"].startswith("###")
        assert chat_messages[0]["content"].endswith("\n###\nDescription:")

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
        assert f">>> {inputs[0]}" in result.stdout
        assert "requests.get" in result.stdout
        assert "localhost:8080" in result.stdout
        assert f">>> {inputs[1]}" in result.stdout
        assert "localhost:443" in result.stdout

        chat_storage = cfg.get("CHAT_CACHE_PATH")
        tmp_chat = Path(chat_storage) / dict_arguments["--repl"]
        chat_messages = json.loads(tmp_chat.read_text())
        assert chat_messages[0]["content"].startswith("###")
        assert chat_messages[0]["content"].endswith("\n###\nCode:")
        assert chat_messages[2]["content"].endswith("\nCode:")

        # Coming back after exit.
        new_inputs = ("Change port to 80", "exit()")
        result = runner.invoke(
            app, self.get_arguments(**dict_arguments), input="\n".join(new_inputs)
        )
        # Should include previous chat history.
        assert "user: ###" in result.stdout
        assert "Chat History" in result.stdout
        assert f"user: {inputs[1]}" in result.stdout

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
        stdout = result.stdout.strip()
        print(stdout)
        # TODO: Fix this test.
        # Not sure how os.system pipes the output to stdout,
        # but it is not part of the result.stdout.
        # assert "command not found" not in result.stdout
        # assert "hello world" in stdout.split("\n")[-1]

    @patch("sgpt.client.OpenAIClient.get_completion")
    def test_model_option(self, mocked_get_completion):
        dict_arguments = {
            "prompt": "What is the capital of the Czech Republic?",
            "--model": "gpt-4",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        mocked_get_completion.assert_called_once_with(
            messages=ANY,
            model="gpt-4",
            temperature=0.1,
            top_probability=1.0,
            caching=False,
        )
        assert result.exit_code == 0

    def test_color_output(self):
        color = cfg.get("DEFAULT_COLOR")
        role = SystemRole.get("default")
        handler = Handler(role=role)
        assert handler.color == color
        os.environ["DEFAULT_COLOR"] = "red"
        handler = Handler(role=role)
        assert handler.color == "red"

    def test_simple_stdin(self):
        result = runner.invoke(app, input="What is the capital of Germany?\n")
        assert "Berlin" in result.stdout

    def test_shell_stdin_with_prompt(self):
        dict_arguments = {
            "prompt": "Sort by name",
            "--shell": True,
        }
        stdin = "What is in current folder\n"
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=stdin)
        assert result.stdout == "ls | sort\n"

    def test_role(self):
        test_role = Path(cfg.get("ROLE_STORAGE_PATH")) / "test_json.json"
        test_role.unlink(missing_ok=True)
        dict_arguments = {
            "prompt": "test",
            "--create-role": "test_json",
        }
        input = "You are a JSON generator, return only JSON as response.\n" "json\n"
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=input)
        assert result.exit_code == 0

        dict_arguments = {
            "prompt": "test",
            "--list-roles": True,
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "test_json" in result.stdout

        dict_arguments = {
            "prompt": "test",
            "--show-role": "test_json",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "You are a JSON generator" in result.stdout

        # Test with command line argument prompt.
        dict_arguments = {
            "prompt": "random username, password, email",
            "--role": "test_json",
        }
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        generated_json = json.loads(result.stdout)
        assert "username" in generated_json
        assert "password" in generated_json
        assert "email" in generated_json

        # Test with stdin prompt.
        dict_arguments = {
            "prompt": "",
            "--role": "test_json",
        }
        stdin = "random username, password, email"
        result = runner.invoke(app, self.get_arguments(**dict_arguments), input=stdin)
        assert result.exit_code == 0
        generated_json = json.loads(result.stdout)
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
        #     assert word in result.stdout
