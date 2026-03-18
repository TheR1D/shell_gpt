"""Unit tests for MiniMax provider integration."""

import os
from unittest.mock import patch

from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, comp_args, mock_comp, runner

role = SystemRole.get(DefaultRoles.DEFAULT.value)


@patch("sgpt.handlers.handler.completion")
def test_minimax_model_temperature_clamping(completion):
    """MiniMax models should have temperature clamped from 0.0 to 0.01."""
    completion.return_value = mock_comp("Hello from MiniMax")

    args = {
        "prompt": "say hello",
        "--model": "MiniMax-M2.7",
    }
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    assert "Hello from MiniMax" in result.output
    # Default temperature is 0.0, but MiniMax requires > 0.0
    call_kwargs = completion.call_args
    assert call_kwargs[1]["temperature"] == 0.01 or call_kwargs.kwargs.get("temperature") == 0.01


@patch("sgpt.handlers.handler.completion")
def test_minimax_model_nonzero_temperature_unchanged(completion):
    """Non-zero temperature should pass through unchanged for MiniMax models."""
    completion.return_value = mock_comp("Creative output")

    args = {
        "prompt": "be creative",
        "--model": "MiniMax-M2.7",
        "--temperature": "0.7",
    }
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    call_kwargs = completion.call_args
    assert call_kwargs[1]["temperature"] == 0.7 or call_kwargs.kwargs.get("temperature") == 0.7


@patch("sgpt.handlers.handler.completion")
def test_minimax_highspeed_model(completion):
    """MiniMax-M2.7-highspeed should also get temperature clamping."""
    completion.return_value = mock_comp("Fast response")

    args = {
        "prompt": "quick answer",
        "--model": "MiniMax-M2.7-highspeed",
    }
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    assert "Fast response" in result.output
    call_kwargs = completion.call_args
    assert call_kwargs[1]["temperature"] == 0.01 or call_kwargs.kwargs.get("temperature") == 0.01


@patch("sgpt.handlers.handler.completion")
def test_minimax_m25_model_still_works(completion):
    """Previous MiniMax-M2.5 model should still work with temperature clamping."""
    completion.return_value = mock_comp("M2.5 response")

    args = {
        "prompt": "say hello",
        "--model": "MiniMax-M2.5",
    }
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    assert "M2.5 response" in result.output
    call_kwargs = completion.call_args
    assert call_kwargs[1]["temperature"] == 0.01 or call_kwargs.kwargs.get("temperature") == 0.01


@patch("sgpt.handlers.handler.completion")
def test_non_minimax_model_zero_temperature(completion):
    """Non-MiniMax models should keep temperature=0.0 unchanged."""
    completion.return_value = mock_comp("Berlin")

    args = {
        "prompt": "capital of Germany?",
        "--model": "gpt-4o",
    }
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    call_kwargs = completion.call_args
    assert call_kwargs[1]["temperature"] == 0.0 or call_kwargs.kwargs.get("temperature") == 0.0


@patch("sgpt.handlers.handler.completion")
def test_minimax_chat_mode(completion):
    """MiniMax should work in chat mode with temperature clamping."""
    from pathlib import Path

    from sgpt.config import cfg

    completion.side_effect = [mock_comp("ok"), mock_comp("42")]
    chat_name = "_test_minimax"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {
        "prompt": "remember number 40",
        "--chat": chat_name,
        "--model": "MiniMax-M2.7",
    }
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "ok" in result.output

    args["prompt"] = "add 2 to it"
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "42" in result.output

    # Verify temperature was clamped in both calls
    for call in completion.call_args_list:
        temp = call[1].get("temperature", call.kwargs.get("temperature"))
        assert temp == 0.01

    chat_path.unlink(missing_ok=True)
