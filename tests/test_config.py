import os
from pathlib import Path
import pytest
from unittest.mock import patch
from sgpt.config import resolve_config_path

# Mock API key to prevent Config class from asking for it via getpass.
os.environ["OPENAI_API_KEY"] = "sk-test"

@pytest.fixture(autouse=True)
def mock_os_name(monkeypatch):
    # Override the global fixture to use the real os.name
    # This prevents pathlib from failing on Windows when os.name is "test"
    monkeypatch.setattr(os, "name", "nt" if os.name == "nt" else "posix")

def test_resolve_config_path_new_exists(monkeypatch):
    mock_folder = Path("C:/temp/shell_gpt") if os.name == "nt" else Path("/tmp/shell_gpt")
    monkeypatch.setattr("sgpt.config.SHELL_GPT_CONFIG_FOLDER", mock_folder)

    new_path = mock_folder / "sgptrc"
    old_path = mock_folder / ".sgptrc"

    # Use monkeypatch to mock Path.exists
    monkeypatch.setattr(Path, "exists", lambda self: self == new_path)
    assert resolve_config_path() == new_path

def test_resolve_config_path_old_exists(monkeypatch):
    mock_folder = Path("C:/temp/shell_gpt") if os.name == "nt" else Path("/tmp/shell_gpt")
    monkeypatch.setattr("sgpt.config.SHELL_GPT_CONFIG_FOLDER", mock_folder)

    new_path = mock_folder / "sgptrc"
    old_path = mock_folder / ".sgptrc"

    # Use monkeypatch to mock Path.exists
    # If self is new_path, return False. If self is old_path, return True.
    def mock_exists(self):
        if self == new_path:
            return False
        if self == old_path:
            return True
        return False

    monkeypatch.setattr(Path, "exists", mock_exists)
    assert resolve_config_path() == old_path

def test_resolve_config_path_none_exists(monkeypatch):
    mock_folder = Path("C:/temp/shell_gpt") if os.name == "nt" else Path("/tmp/shell_gpt")
    monkeypatch.setattr("sgpt.config.SHELL_GPT_CONFIG_FOLDER", mock_folder)

    new_path = mock_folder / "sgptrc"
    old_path = mock_folder / ".sgptrc"

    # Use monkeypatch to mock Path.exists
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert resolve_config_path() == new_path
