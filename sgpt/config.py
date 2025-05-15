import os
from getpass import getpass
from pathlib import Path
from tempfile import gettempdir
from typing import Any
import sys # For stderr in _get_default_suggested_vertex_models

from click import UsageError

CONFIG_FOLDER = os.path.expanduser("~/.config")
SHELL_GPT_CONFIG_FOLDER = Path(CONFIG_FOLDER) / "shell_gpt"
SHELL_GPT_CONFIG_PATH = SHELL_GPT_CONFIG_FOLDER / ".sgptrc"
ROLE_STORAGE_PATH = SHELL_GPT_CONFIG_FOLDER / "roles"
FUNCTIONS_PATH = SHELL_GPT_CONFIG_FOLDER / "functions"
CHAT_CACHE_PATH = Path(gettempdir()) / "chat_cache"
CACHE_PATH = Path(gettempdir()) / "cache"

# Definition of _get_default_suggested_vertex_models must come BEFORE DEFAULT_CONFIG
def _get_default_suggested_vertex_models() -> str:
    """
    Tries to determine a list of suggested Vertex AI models by inspecting
    LiteLLM's model_cost data. Falls back to a hardcoded list if LiteLLM
    is not available or an error occurs.
    """
    try:
        import litellm  # Try to import litellm

        # model_cost should be populated after 'import litellm'
        if hasattr(litellm, "model_cost") and litellm.model_cost:
            vertex_ai_models = set()  # Use a set to handle duplicates naturally
            for model_name, model_info in litellm.model_cost.items():
                if isinstance(model_info, dict) and model_info.get(
                    "litellm_provider"
                ) == "vertex_ai":
                    # Check if the model_name from litellm.model_cost is already
                    # a fully qualified LiteLLM model string for Vertex AI.
                    if model_name.startswith("vertex_ai/") or model_name.startswith(
                        "google/"
                    ):
                        vertex_ai_models.add(model_name)
                    else:
                        # For base model names (e.g., "gemini-1.5-pro-preview-05-06"),
                        # construct the prefixed versions that sgpt uses.
                        vertex_ai_models.add(f"google/{model_name}")
                        vertex_ai_models.add(f"vertex_ai/{model_name}")

            if vertex_ai_models:
                return ",".join(sorted(list(vertex_ai_models)))
    except ImportError:
        # LiteLLM is not installed.
        pass
    except Exception as e:
        # Catch any other unexpected errors during processing.
        print(
            f"sgpt: Debug: Error determining Vertex AI models from LiteLLM: {e}",
            file=sys.stderr,
        )
        pass

    # Fallback if LiteLLM not installed or models can't be determined
    return "google/gemini-2.5-pro-preview-05-06,google/gemini-1.5-pro-latest,google/gemini-1.5-flash-latest"

# DEFAULT_CONFIG must be defined after _get_default_suggested_vertex_models
DEFAULT_CONFIG = {
    # TODO: Refactor ENV variables with SGPT_ prefix.
    # TODO: Refactor it to CHAT_STORAGE_PATH.
    "CHAT_CACHE_PATH": os.getenv("CHAT_CACHE_PATH", str(CHAT_CACHE_PATH)),
    "CACHE_PATH": os.getenv("CACHE_PATH", str(CACHE_PATH)),
    "CHAT_CACHE_LENGTH": int(os.getenv("CHAT_CACHE_LENGTH", "100")),
    "CACHE_LENGTH": int(os.getenv("CHAT_CACHE_LENGTH", "100")),
    "REQUEST_TIMEOUT": int(os.getenv("REQUEST_TIMEOUT", "60")),
    "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL", "gpt-4o"),
    "DEFAULT_COLOR": os.getenv("DEFAULT_COLOR", "magenta"),
    "ROLE_STORAGE_PATH": os.getenv("ROLE_STORAGE_PATH", str(ROLE_STORAGE_PATH)),
    "DEFAULT_EXECUTE_SHELL_CMD": os.getenv("DEFAULT_EXECUTE_SHELL_CMD", "false"),
    "DISABLE_STREAMING": os.getenv("DISABLE_STREAMING", "false"),
    "CODE_THEME": os.getenv("CODE_THEME", "dracula"),
    "OPENAI_FUNCTIONS_PATH": os.getenv("OPENAI_FUNCTIONS_PATH", str(FUNCTIONS_PATH)),
    "OPENAI_USE_FUNCTIONS": os.getenv("OPENAI_USE_FUNCTIONS", "true"),
    "SHOW_FUNCTIONS_OUTPUT": os.getenv("SHOW_FUNCTIONS_OUTPUT", "false"),
    "API_BASE_URL": os.getenv("API_BASE_URL", "default"),
    "PRETTIFY_MARKDOWN": os.getenv("PRETTIFY_MARKDOWN", "true"),
    "USE_LITELLM": os.getenv("USE_LITELLM", "true"),
    "SHELL_INTERACTION": os.getenv("SHELL_INTERACTION ", "true"),
    "OS_NAME": os.getenv("OS_NAME", "auto"),
    "SHELL_NAME": os.getenv("SHELL_NAME", "auto"),
    "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT", "DISABLED_SGPT_SETUP_ENTER_YOUR_GCP_PROJECT_ID"),
    "VERTEXAI_LOCATION": os.getenv("VERTEXAI_LOCATION", "DISABLED_SGPT_SETUP_ENTER_YOUR_GCP_LOCATION"),
    # Dynamically determine suggested Vertex AI models, with a fallback.
    "SUGGESTED_VERTEXAI_MODELS": os.getenv(
        "SUGGESTED_VERTEXAI_MODELS", _get_default_suggested_vertex_models()
    ),
    # New features might add their own config variables here.
}


class Config(dict):  # type: ignore
    def __init__(self, config_path: Path, **defaults: Any):
        self.config_path = config_path

        if self._exists:
            self._read()
            has_new_config = False
            for key, value in defaults.items():
                if key not in self:
                    has_new_config = True
                    self[key] = value
            if has_new_config:
                self._write()
        else:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Don't write API key to config file if it is in the environment.
            if not defaults.get("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
                __api_key = getpass(prompt="Please enter your OpenAI API key: ")
                defaults["OPENAI_API_KEY"] = __api_key
            super().__init__(**defaults)
            self._write()

    @property
    def _exists(self) -> bool:
        return self.config_path.exists()

    def _write(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as file:
            string_config = ""
            for key, value in self.items():
                string_config += f"{key}={value}\n"
            file.write(string_config)

    def _read(self) -> None:
        with open(self.config_path, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    self[key] = value

    def get(self, key: str) -> str:  # type: ignore
        # Prioritize environment variables over config file.
        value = os.getenv(key) or super().get(key)
        if not value:
            raise UsageError(f"Missing config key: {key}")
        return value


cfg = Config(SHELL_GPT_CONFIG_PATH, **DEFAULT_CONFIG)
