import json
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, cast

from click import UsageError
from rich.live_render import VerticalOverflowMethod

from ..cache import Cache
from ..config import cfg
from ..function import get_function
from ..printer import MarkdownPrinter, Printer, TextPrinter
from ..providers import resolve
from ..role import DefaultRoles, SystemRole

completion: Callable[..., Any] = lambda *args, **kwargs: Generator[Any, None, None]

use_litellm = cfg.get("USE_LITELLM") == "true"
additional_kwargs: Dict[str, Any] = {}


def _provider_kwargs() -> Dict[str, Any]:
    """Connection settings for the provider resolved at call time."""
    provider = resolve()
    key = provider.api_key()
    if not key:
        raise UsageError(
            f"Missing API key: set {provider.api_key_env or 'OPENAI_API_KEY'} "
            "or run 'sgpt setup test'."
        )
    return {
        "timeout": int(cfg.get("REQUEST_TIMEOUT")),
        "api_key": key,
        "base_url": provider.base_url or None,
    }


if use_litellm:
    import litellm  # type: ignore

    completion = litellm.completion
    litellm.suppress_debug_info = True
    # shortcut: resolved at import, so --provider does not apply with USE_LITELLM
    additional_kwargs = _provider_kwargs()
else:
    from openai import OpenAI

    _client: Any = None

    def completion(*args: Any, **kwargs: Any) -> Any:
        """Build the client on first use, once the provider is settled."""
        global _client
        if _client is None:
            _client = OpenAI(**_provider_kwargs())
        return _client.chat.completions.create(*args, **kwargs)


class Handler:
    cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))

    def __init__(self, role: SystemRole, markdown: bool) -> None:
        self.role = role

        self.base_url = resolve().base_url or None
        self.timeout = int(cfg.get("REQUEST_TIMEOUT"))

        self.markdown = "APPLY MARKDOWN" in self.role.role and markdown
        self.code_theme, self.color = cfg.get("CODE_THEME"), cfg.get("DEFAULT_COLOR")

    @property
    def printer(self) -> Printer:
        vertical_overflow = cast(
            VerticalOverflowMethod, cfg.get("MARKDOWN_LIVE_VERTICAL_OVERFLOW")
        )
        refresh_interval = float(cfg.get("MARKDOWN_LIVE_REFRESH_INTERVAL"))
        return (
            MarkdownPrinter(self.code_theme, refresh_interval, vertical_overflow)
            if self.markdown
            else TextPrinter(self.color)
        )

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def handle_function_call(
        self,
        messages: List[dict[str, Any]],
        tool_call_id: str,
        name: str,
        arguments: str,
    ) -> Generator[str, None, None]:
        # Add assistant message with tool call
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {"name": name, "arguments": arguments},
                    }
                ],
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

        # Add tool response message
        messages.append(
            {"role": "tool", "content": result, "tool_call_id": tool_call_id}
        )

    @cache
    def get_completion(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
    ) -> Generator[str, None, None]:
        tool_call_id = name = arguments = ""
        is_shell_role = self.role.name == DefaultRoles.SHELL.value
        is_code_role = self.role.name == DefaultRoles.CODE.value
        is_dsc_shell_role = self.role.name == DefaultRoles.DESCRIBE_SHELL.value
        if is_shell_role or is_code_role or is_dsc_shell_role:
            functions = None

        if functions:
            additional_kwargs["tool_choice"] = "auto"
            additional_kwargs["tools"] = functions
            additional_kwargs["parallel_tool_calls"] = False

        response = completion(
            model=model,
            temperature=temperature,
            top_p=top_p,
            messages=messages,
            stream=True,
            **additional_kwargs,
        )

        try:
            for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # LiteLLM uses dict instead of Pydantic object like OpenAI does.
                tool_calls = (
                    delta.get("tool_calls") if use_litellm else delta.tool_calls
                )
                if tool_calls:
                    for tool_call in tool_calls:
                        if use_litellm:
                            # TODO: test.
                            tool_call_id = tool_call.get("id") or tool_call_id
                            name = tool_call.get("function", {}).get("name") or name
                            arguments += tool_call.get("function", {}).get(
                                "arguments", ""
                            )
                        else:
                            tool_call_id = tool_call.id or tool_call_id
                            name = tool_call.function.name or name
                            arguments += tool_call.function.arguments or ""
                if chunk.choices[0].finish_reason == "tool_calls":
                    yield from self.handle_function_call(
                        messages, tool_call_id, name, arguments
                    )
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
