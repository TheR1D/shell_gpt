import json
import os # Added import for os module
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

from ..cache import Cache
from ..config import cfg
from ..function import get_function
from ..printer import MarkdownPrinter, Printer, TextPrinter
from ..role import DefaultRoles, SystemRole

completion: Callable[..., Any] = lambda *args, **kwargs: Generator[Any, None, None]

base_url = cfg.get("API_BASE_URL")
use_litellm = cfg.get("USE_LITELLM") == "true"
additional_kwargs = {
    "timeout": int(cfg.get("REQUEST_TIMEOUT")),
    "api_key": cfg.get("OPENAI_API_KEY"),
    "base_url": None if base_url == "default" else base_url,
}

if use_litellm:
    import litellm  # type: ignore

    completion = litellm.completion
    litellm.suppress_debug_info = True
    additional_kwargs.pop("api_key")
else:
    from openai import OpenAI

    client = OpenAI(**additional_kwargs)  # type: ignore
    completion = client.chat.completions.create
    additional_kwargs = {}


class Handler:
    cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))

    def __init__(self, role: SystemRole, markdown: bool) -> None:
        self.role = role

        api_base_url = cfg.get("API_BASE_URL")
        self.base_url = None if api_base_url == "default" else api_base_url
        self.timeout = int(cfg.get("REQUEST_TIMEOUT"))

        self.markdown = "APPLY MARKDOWN" in self.role.role and markdown
        self.code_theme, self.color = cfg.get("CODE_THEME"), cfg.get("DEFAULT_COLOR")

    @property
    def printer(self) -> Printer:
        return (
            MarkdownPrinter(self.code_theme)
            if self.markdown
            else TextPrinter(self.color)
        )

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def handle_function_call(
        self,
        messages: List[dict[str, Any]],
        name: str,
        arguments: str,
    ) -> Generator[str, None, None]:
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "function_call": {"name": name, "arguments": arguments},
            }
        )

        if messages and messages[-1]["role"] == "assistant":
            yield "\n"

        dict_args = json.loads(arguments)
        joined_args = ", ".join(f'{k}="{v}"' for k, v in dict_args.items())
        yield f"> @FunctionCall `{name}({joined_args})` \n\n"

        result = get_function(name)(**dict_args)
        if cfg.get("SHOW_FUNCTIONS_OUTPUT") == "true":
            yield f"```text\n{result}\n```\n"
        messages.append({"role": "function", "content": result, "name": name})

    @cache
    def get_completion(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
        # **kwargs will be passed from self.handle, containing caching=True/False
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        name = arguments = ""
        is_shell_role = self.role.name == DefaultRoles.SHELL.value
        is_code_role = self.role.name == DefaultRoles.CODE.value
        is_dsc_shell_role = self.role.name == DefaultRoles.DESCRIBE_SHELL.value
        if is_shell_role or is_code_role or is_dsc_shell_role:
            functions = None

        # Create a copy of the global additional_kwargs to modify for this specific call.
        current_call_kwargs = additional_kwargs.copy()
        # Ensure api_key is not in current_call_kwargs if using LiteLLM, as it's handled by LiteLLM.
        if use_litellm and "api_key" in current_call_kwargs:
            del current_call_kwargs["api_key"]


        if functions:
            current_call_kwargs["tool_choice"] = "auto"
            # Debug print removed.
            current_call_kwargs["tools"] = functions
            # Only set parallel_tool_calls for non-Vertex AI models,
            # as Vertex AI (Gemini) via LiteLLM doesn't support it.
            # This logic might need refinement based on which Vertex AI path is taken.
            if use_litellm and model and not (model.startswith("vertex_ai") or model.startswith("google/") or model.startswith("vertex-genai/")):
                current_call_kwargs["parallel_tool_calls"] = False
            elif not use_litellm: # If using OpenAI directly, it's a valid param
                current_call_kwargs["parallel_tool_calls"] = False

        transformed_model_for_litellm = model
        is_vertex_genai_model = False

        if use_litellm and model:
            gcp_project_id = cfg.get("GOOGLE_CLOUD_PROJECT")
            gcp_location = cfg.get("VERTEXAI_LOCATION")
            valid_gcp_project = gcp_project_id and not gcp_project_id.startswith("DISABLED_SGPT_SETUP") and gcp_project_id.strip() not in ('""', '')
            valid_gcp_location = gcp_location and not gcp_location.startswith("DISABLED_SGPT_SETUP") and gcp_location.strip() not in ('""', '')

            if model.startswith("vertex-genai/"):
                # Route this through LiteLLM's standard Vertex AI provider
                # by transforming the model name. This avoids google-genai SDK complexities via LiteLLM.
                is_vertex_genai_model = True # Still useful for the finally block if we re-add env var logic later
                base_model_name = model.split('/', 1)[1]
                # Transform to a prefix LiteLLM understands for its native Vertex AI integration
                transformed_model_for_litellm = f"vertex_ai/{base_model_name}"
                if valid_gcp_project:
                    current_call_kwargs["project"] = gcp_project_id
                if valid_gcp_location:
                    current_call_kwargs["location"] = gcp_location
                # Debug prints removed.
                # No longer setting GOOGLE_GENAI_USE_VERTEXAI as we are using LiteLLM's google-cloud-aiplatform path

            elif model.startswith("vertex_ai/") or model.startswith("google/"):
                # This is the existing path for LiteLLM's default Vertex AI provider (google-cloud-aiplatform)
                if valid_gcp_project:
                    current_call_kwargs["project"] = gcp_project_id
                if valid_gcp_location:
                    current_call_kwargs["location"] = gcp_location
                # Debug prints removed.


        try:
            response = completion(
                model=transformed_model_for_litellm,
                temperature=temperature,
                top_p=top_p,
                messages=messages,
                stream=True,
                **current_call_kwargs,
            )
        finally:
            # Clean up GOOGLE_GENAI_USE_VERTEXAI if it was set by a different path or future logic
            # For now, this specific vertex-genai path doesn't set it.
            if os.getenv("GOOGLE_GENAI_USE_VERTEXAI"): # Check if it was set by any chance
                 os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
                 # Debug print removed.

        try:
            for chunk in response:
                delta = chunk.choices[0].delta

                # LiteLLM uses dict instead of Pydantic object like OpenAI does.
                tool_calls = (
                    delta.get("tool_calls") if use_litellm else delta.tool_calls
                )
                if tool_calls:
                    for tool_call in tool_calls:
                        if tool_call.function.name:
                            name = tool_call.function.name
                        if tool_call.function.arguments:
                            arguments += tool_call.function.arguments
                if chunk.choices[0].finish_reason == "tool_calls":
                    yield from self.handle_function_call(messages, name, arguments)
                    yield from self.get_completion(
                        model=model,
                        temperature=temperature,
                        top_p=top_p,
                        messages=messages,
                        functions=functions,
                        caching=False,
                    )
                    return

                yield delta.content or ""
        except KeyboardInterrupt:
            response.close()

    def handle(
        self,
        prompt: str,
        model: str,
        temperature: float,
        top_p: float,
        caching: bool,
        functions: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> str:
        disable_stream = cfg.get("DISABLE_STREAMING") == "true"
        messages = self.make_messages(prompt.strip())
        generator = self.get_completion(
            model=model,
            temperature=temperature,
            top_p=top_p,
            messages=messages,
            functions=functions,
            caching=caching,
            **kwargs,
        )
        return self.printer(generator, not disable_stream)
