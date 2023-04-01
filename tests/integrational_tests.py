"""
This test module will execute real commands using shell.
This means it will call sgpt.py with command line arguments.
Make sure you have your API key in place ~/.config/shell_gpt/.sgptrc
or ENV variable OPENAI_API_KEY.
It is useful for quick tests, saves a bit time.
"""

import subprocess
import os
from time import sleep
from unittest import TestCase
from tempfile import NamedTemporaryFile
from uuid import uuid4

import typer
from typer.testing import CliRunner
from sgpt import main

runner = CliRunner()
app = typer.Typer()
app.command()(main)


class TestShellGpt(TestCase):
    def setUp(self) -> None:
        # Just to not spam the API.
        sleep(2)

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

    def test_code(self):
        """
        This test will request from ChatGPT a python code to make CLI app,
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
                assert False, "The output is not valid Python code."
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

    def test_list_chat(self):
        result = runner.invoke(app, ["--list-chat"])
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
