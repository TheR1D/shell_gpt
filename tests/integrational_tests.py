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

import typer
from typer.testing import CliRunner
from sgpt import main

runner = CliRunner()
app = typer.Typer()
app.command()(main)


class TestCliApp(TestCase):
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
        return arguments

    def test_simple_queries(self):
        dict_arguments = {"prompt": "What is the capital of the Czech Republic?"}
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "Prague" in result.stdout

    def test_shell_queries(self):
        dict_arguments = {"prompt": "make a commit using git", "--shell": True}
        result = runner.invoke(app, self.get_arguments(**dict_arguments))
        assert result.exit_code == 0
        assert "git commit" in result.stdout

    def test_code_queries(self):
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
