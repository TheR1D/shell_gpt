import json
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, cast

from click import UsageError
from rich.live_render import VerticalOverflowMethod

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


def _parse_api_extra_body(raw: str) -> Optional[Dict[str, Any]]:
    """Parse the API_EXTRA_BODY config string. Empty -> None; bad input -> UsageError."""
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UsageError(f"Invalid JSON in API_EXTRA_BODY: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise UsageError("API_EXTRA_BODY must be a JSON object")
    return parsed


def _apply_api_extra_body(
    kwargs: Dict[str, Any], body: Optional[Dict[str, Any]], litellm_mode: bool
) -> None:
    """Merge API_EXTRA_BODY into kwargs. OpenAI takes ``extra_body``; litellm gets a merge."""
    if not body:
        return
    if litellm_mode:
        kwargs.update(body)
    else:
        kwargs["extra_body"] = body


def filter_thinking_tokens(stream: Iterable[str]) -> Generator[str, None, None]:
    """Strip ``<think>...</think>`` and ``<thinking>...</thinking>`` from a string stream.

    Handles tags split across chunks. Yields nothing for an unterminated block.
    When no tag appears, output concatenated is byte-identical to input.
    """
    _OPEN = ("<think>", "<thinking>")
    _CLOSE = ("</think>", "</thinking>")
    _ALL = _OPEN + _CLOSE

    def _matches(candidate: str, tags: Iterable[str]) -> bool:
        return any(tag.startswith(candidate) for tag in tags)

    inside = False
    buffer = ""

    for chunk in stream:
        if not chunk:
            continue
        for char in chunk:
            if not inside:
                if not buffer:
                    if char == "<":
                        buffer = "<"
                    else:
                        yield char
                else:
                    candidate = buffer + char
                    if candidate in _OPEN:
                        inside = True
                        buffer = ""
                    elif _matches(candidate, _ALL):
                        buffer = candidate
                    else:
                        yield buffer + char
                        buffer = ""
            else:
                if not buffer:
                    if char == "<":
                        buffer = "<"
                else:
                    candidate = buffer + char
                    if candidate in _CLOSE:
                        inside = False
                        buffer = ""
                    elif _matches(candidate, _CLOSE):
                        buffer = candidate
                    else:
                        buffer = ""
    if buffer and not inside:
        yield buffer


def _make_thinking_filter() -> Callable[[str], Generator[str, None, None]]:
    """Stateful filter for streaming: tag-buffer survives across chunks.

    Returns a function that, given a content chunk, yields filtered chars.
    State (buffer, inside) lives in the closure and persists between calls.
    Unterminated thinking block at end-of-stream is discarded.
    """
    _OPEN = ("<think>", "<thinking>")
    _CLOSE = ("</think>", "</thinking>")
    _ALL = _OPEN + _CLOSE

    def _matches(candidate: str, tags: Iterable[str]) -> bool:
        return any(tag.startswith(candidate) for tag in tags)

    buffer = ""
    inside = False

    def feed(chunk: str) -> Generator[str, None, None]:
        nonlocal buffer, inside
        for char in chunk:
            if not inside:
                if not buffer:
                    if char == "<":
                        buffer = "<"
                    else:
                        yield char
                else:
                    candidate = buffer + char
                    if candidate in _OPEN:
                        inside = True
                        buffer = ""
                    elif _matches(candidate, _ALL):
                        buffer = candidate
                    else:
                        yield buffer + char
                        buffer = ""
            else:
                if not buffer:
                    if char == "<":
                        buffer = "<"
                else:
                    candidate = buffer + char
                    if candidate in _CLOSE:
                        inside = False
                        buffer = ""
                    elif _matches(candidate, _CLOSE):
                        buffer = candidate
                    else:
                        buffer = ""
        if buffer and not inside:
            yield buffer
            buffer = ""

    return feed


try:
    _api_extra_body_raw = cfg.get("API_EXTRA_BODY")
except UsageError:
    _api_extra_body_raw = ""
_api_extra_body: Optional[Dict[str, Any]] = _parse_api_extra_body(_api_extra_body_raw)

if use_litellm:
    import litellm  # type: ignore

    completion = litellm.completion
    litellm.suppress_debug_info = True
    _apply_api_extra_body(additional_kwargs, _api_extra_body, True)
else:
    from openai import OpenAI

    client = OpenAI(**additional_kwargs)  # type: ignore
    completion = client.chat.completions.create
    additional_kwargs = {}
    _apply_api_extra_body(additional_kwargs, _api_extra_body, False)


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
        thinking_filter = _make_thinking_filter()
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

                content = delta.get("content") if use_litellm else delta.content
                if content:
                    yield from thinking_filter(content)
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
