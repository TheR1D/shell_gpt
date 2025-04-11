import json
import re
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
        self.is_shell = role.name == DefaultRoles.SHELL.value

        api_base_url = cfg.get("API_BASE_URL")
        self.base_url = None if api_base_url == "default" else api_base_url
        self.timeout = int(cfg.get("REQUEST_TIMEOUT"))

        self.markdown = "APPLY MARKDOWN" in self.role.role and markdown
        self.code_theme, self.color = cfg.get("CODE_THEME"), cfg.get("DEFAULT_COLOR")

        self.backticks_start = re.compile(r"(^|[\r\n]+)```\w*[\r\n]+")
        end_regex_parts = [r"[\r\n]+", "`", "`", "`", r"([\r\n]+|$)"]
        self.backticks_end_prefixes = [
            re.compile("".join(end_regex_parts[: i + 1]))
            for i in range(len(end_regex_parts))
        ]

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

    def _matches_end_at(self, text: str) -> tuple[bool, int]:
        end_of_match = 0
        for _i, regex in enumerate(self.backticks_end_prefixes):
            m = regex.search(text)
            if m:
                end_of_match = m.end()
            else:
                return False, end_of_match
        return True, m.start()

    def _filter_chunks(
        self, chunks: Generator[str, None, None]
    ) -> Generator[str, None, None]:
        buffer = ""
        inside_backticks = False
        end_of_beginning = 0

        for chunk in chunks:
            buffer += chunk
            if not inside_backticks:
                m = self.backticks_start.search(buffer)
                if not m:
                    continue
                new_end_of_beginning = m.end()
                if new_end_of_beginning > end_of_beginning:
                    end_of_beginning = new_end_of_beginning
                    continue
                inside_backticks = True
                buffer = buffer[end_of_beginning:]
            if inside_backticks:
                matches_end, index = self._matches_end_at(buffer)
                if matches_end:
                    yield buffer[:index]
                    return
                if index == len(buffer):
                    continue
                else:
                    yield buffer
                    buffer = ""
        if buffer:
            yield buffer

    @cache
    def get_completion(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
    ) -> Generator[str, None, None]:
        name = arguments = ""
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
        if self.role.name == DefaultRoles.SHELL.value:
            generator = self._filter_chunks(generator)
        return self.printer(generator, not disable_stream)
