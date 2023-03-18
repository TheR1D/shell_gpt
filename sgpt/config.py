import os
from pathlib import Path
from getpass import getpass
from tempfile import gettempdir

from click import UsageError

CONFIG_FOLDER = os.path.expanduser("~/.config")
CONFIG_PATH = Path(CONFIG_FOLDER) / "shell_gpt" / ".sgptrc"
CHAT_CACHE_PATH = Path(gettempdir()) / "shell_gpt" / "chat_cache"
CACHE_PATH = Path(gettempdir()) / "shell_gpt" / "cache"
CHAT_CACHE_LENGTH = 100
CACHE_LENGTH = 100
REQUEST_TIMEOUT = 60
EXPECTED_KEYS = (
    "OPENAI_API_HOST",
    "OPENAI_API_KEY",
    "CHAT_CACHE_LENGTH",
    "CHAT_CACHE_PATH",
    "CACHE_LENGTH",
    "CACHE_PATH",
    "REQUEST_TIMEOUT",
)
config = {}


def init() -> None:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # If user has ENV API key, don't write it to config file.
        api_key = os.getenv("OPENAI_API_KEY") or getpass(prompt="Please enter your OpenAI API key: ")
        config["OPENAI_API_KEY"] = api_key
        config["OPENAI_API_HOST"] = os.getenv("OPENAI_API_HOST", "https://api.openai.com")
        config["CHAT_CACHE_LENGTH"] = os.getenv("CHAT_CACHE_LENGTH", str(CHAT_CACHE_LENGTH))
        config["CHAT_CACHE_PATH"] = os.getenv("CHAT_CACHE_PATH", str(CHAT_CACHE_PATH))
        config["CACHE_LENGTH"] = os.getenv("CACHE_LENGTH", str(CACHE_LENGTH))
        config["CACHE_PATH"] = os.getenv("CACHE_PATH", str(CACHE_PATH))
        config["REQUEST_TIMEOUT"] = os.getenv("REQUEST_TIMEOUT", str(REQUEST_TIMEOUT))
        _write()

    with open(CONFIG_PATH, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=")
                config[key] = value


def get(key: str) -> str:
    # Prioritize ENV variables.
    value = os.getenv(key) or config.get(key)
    assert value, UsageError(f"Config missing: {key}.")
    return value


def _write() -> None:
    with open(CONFIG_PATH, "w") as file:
        for key, value in config.items():
            # Write only keys which are not presented in ENV.
            if key in os.environ:
                continue
            file.write(f"{key}={value}\n")


def put(key: str, value: str, write_file=True) -> None:
    config[key] = value
    if not write_file:
        return
    _write()


init()
