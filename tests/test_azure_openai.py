import os
from unittest.mock import patch

import typer
from typer.testing import CliRunner

from sgpt import config, main
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, comp_args, mock_azure_comp, runner

role = SystemRole.get(DefaultRoles.DEFAULT.value)
cfg = config.cfg


@patch("sgpt.handlers.handler.completion")
def test_azure_openai_provider(completion):
    """Test that Azure OpenAI provider works correctly."""
    completion.return_value = mock_azure_comp("Azure OpenAI response")
    
    # Set environment variable for Azure OpenAI provider
    os.environ["OPENAI_PROVIDER"] = "azure-openai"
    
    args = {"prompt": "test prompt"}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "Azure OpenAI response" in result.stdout
    
    # Clean up environment variable
    os.environ.pop("OPENAI_PROVIDER", None)


@patch("sgpt.handlers.handler.completion")
def test_azure_openai_shell_command(completion):
    """Test Azure OpenAI provider with shell command generation."""
    completion.return_value = mock_azure_comp("ls -la")
    
    # Set environment variable for Azure OpenAI provider
    os.environ["OPENAI_PROVIDER"] = "azure-openai"
    
    args = {"prompt": "list files", "--shell": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "ls -la" in result.stdout
    
    # Clean up environment variable
    os.environ.pop("OPENAI_PROVIDER", None)


@patch("sgpt.handlers.handler.completion")
def test_azure_openai_code_generation(completion):
    """Test Azure OpenAI provider with code generation."""
    completion.return_value = mock_azure_comp("print('Hello World')")
    
    # Set environment variable for Azure OpenAI provider
    os.environ["OPENAI_PROVIDER"] = "azure-openai"
    
    args = {"prompt": "hello world in python", "--code": True}
    result = runner.invoke(app, cmd_args(**args))

    completion.assert_called_once_with(**comp_args(role, **args))
    assert result.exit_code == 0
    assert "print('Hello World')" in result.stdout
    
    # Clean up environment variable
    os.environ.pop("OPENAI_PROVIDER", None)


@patch("sgpt.handlers.handler.completion")
def test_azure_openai_chat_mode(completion):
    """Test Azure OpenAI provider with chat mode."""
    completion.side_effect = [mock_azure_comp("ok"), mock_azure_comp("4")]
    
    # Set environment variable for Azure OpenAI provider
    os.environ["OPENAI_PROVIDER"] = "azure-openai"
    
    chat_name = "_test_azure"
    chat_path = cfg.get("CHAT_CACHE_PATH") / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "my number is 2", "--chat": chat_name}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "ok" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "my number + 2?"
    result = runner.invoke(app, cmd_args(**args))
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
    completion.assert_called_with(**expected_args)
    assert completion.call_count == 2

    chat_path.unlink()
    
    # Clean up environment variable
    os.environ.pop("OPENAI_PROVIDER", None)


@patch("sgpt.handlers.handler.completion")
def test_provider_configuration(completion):
    """Test that provider configuration is properly read."""
    completion.return_value = mock_azure_comp("test response")
    
    # Test with different provider values
    test_cases = [
        ("azure-openai", "Azure response"),
        ("openai", "OpenAI response"),
    ]
    
    for provider, expected_content in test_cases:
        os.environ["OPENAI_PROVIDER"] = provider
        completion.return_value = mock_azure_comp(expected_content)
        
        args = {"prompt": "test"}
        result = runner.invoke(app, cmd_args(**args))
        
        assert result.exit_code == 0
        assert expected_content in result.stdout
    
    # Clean up environment variable
    os.environ.pop("OPENAI_PROVIDER", None)