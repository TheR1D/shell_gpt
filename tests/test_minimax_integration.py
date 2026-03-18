"""Integration tests for MiniMax provider.

These tests make real API calls to the MiniMax API.
Set MINIMAX_API_KEY environment variable to run them.
Run with: pytest tests/test_minimax_integration.py -v
"""

import os
from unittest import TestCase

import pytest
import typer
from typer.testing import CliRunner

from sgpt.app import main

runner = CliRunner()
app = typer.Typer()
app.command()(main)

requires_minimax = pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY not set",
)


@requires_minimax
class TestMiniMaxIntegration(TestCase):
    """Integration tests that call the real MiniMax API."""

    @staticmethod
    def get_arguments(prompt, **kwargs):
        arguments = [prompt]
        for key, value in kwargs.items():
            arguments.append(key)
            if isinstance(value, bool):
                continue
            arguments.append(value)
        arguments.append("--no-cache")
        arguments.append("--no-functions")
        return arguments

    def test_minimax_m27_default_prompt(self):
        args = {
            "prompt": "What is 2 + 2? Reply with just the number.",
            "--model": "MiniMax-M2.7",
        }
        result = runner.invoke(app, self.get_arguments(**args))
        assert result.exit_code == 0
        assert "4" in result.output

    def test_minimax_m27_code_generation(self):
        args = {
            "prompt": "Write a Python function that returns 42",
            "--model": "MiniMax-M2.7",
            "--code": True,
        }
        result = runner.invoke(app, self.get_arguments(**args))
        assert result.exit_code == 0
        assert "42" in result.output

    def test_minimax_m27_with_temperature(self):
        args = {
            "prompt": "Say hello",
            "--model": "MiniMax-M2.7",
            "--temperature": "0.5",
        }
        result = runner.invoke(app, self.get_arguments(**args))
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0

    def test_minimax_m25_still_works(self):
        args = {
            "prompt": "What is 2 + 2? Reply with just the number.",
            "--model": "MiniMax-M2.5",
        }
        result = runner.invoke(app, self.get_arguments(**args))
        assert result.exit_code == 0
        assert "4" in result.output
