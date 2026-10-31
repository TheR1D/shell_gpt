import os
from pathlib import Path

from sgpt.config import Config


def make_config(tmp_path: Path, content: str) -> Config:
    config_path = tmp_path / ".sgptrc"
    config_path.write_text(content, encoding="utf-8")
    return Config(config_path)


def test_path_values_support_tilde_and_env_vars(tmp_path, monkeypatch):
    monkeypatch.delenv("CACHE_PATH", raising=False)
    monkeypatch.delenv("CHAT_CACHE_PATH", raising=False)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    config = make_config(
        tmp_path,
        "CACHE_PATH=~/sgpt_test_cache\n"
        "CHAT_CACHE_PATH=${HOME}/sgpt_test_chat_cache\n",
    )

    assert os.path.normpath(config.get("CACHE_PATH")) == os.path.normpath(
        os.path.join(str(home), "sgpt_test_cache")
    )
    assert os.path.normpath(config.get("CHAT_CACHE_PATH")) == os.path.normpath(
        os.path.join(str(home), "sgpt_test_chat_cache")
    )


def test_non_path_values_are_not_expanded(tmp_path, monkeypatch):
    monkeypatch.delenv("DEFAULT_MODEL", raising=False)

    config = make_config(
        tmp_path,
        "DEFAULT_MODEL=$HOME/test-model\n"
        "API_BASE_URL=http://localhost:8080/${model}\n",
    )

    assert config.get("DEFAULT_MODEL") == "$HOME/test-model"
    assert config.get("API_BASE_URL") == "http://localhost:8080/${model}"


def test_plain_paths_are_unchanged(tmp_path, monkeypatch):
    monkeypatch.delenv("CACHE_PATH", raising=False)
    monkeypatch.setenv("UNRELATED_VAR", "should_not_appear")

    config = make_config(tmp_path, "CACHE_PATH=/var/cache/sgpt\n")

    assert config.get("CACHE_PATH") == "/var/cache/sgpt"
