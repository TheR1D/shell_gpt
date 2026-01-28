import json
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
    use_responses_api = False
else:
    from openai import OpenAI

    client = OpenAI(**additional_kwargs)  # type: ignore
    # Use the new Responses API instead of Chat Completions API
    completion = client.responses.stream
    additional_kwargs = {}
    use_responses_api = True


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

    def _messages_to_responses_api_format(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Convert Chat Completions API messages format to Responses API format.
        Returns (instructions, input_messages) tuple.
        """
        instructions = ""
        input_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                # System messages become instructions in Responses API
                instructions = content
            elif role == "user":
                # User messages map to "user" type
                input_messages.append({"type": "user", "content": content})
            elif role == "assistant":
                # Assistant messages map to "assistant" type
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    # Assistant message with tool calls
                    input_messages.append(
                        {"type": "assistant", "tool_calls": tool_calls}
                    )
                else:
                    # Regular assistant message
                    input_messages.append({"type": "assistant", "content": content})
            elif role == "tool":
                # Tool result messages map to "tool_result" type
                input_messages.append(
                    {
                        "type": "tool_result",
                        "tool_call_id": msg.get("tool_call_id"),
                        "content": content,
                    }
                )

        return instructions, input_messages

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

        if use_responses_api:
            # New Responses API path
            yield from self._get_completion_responses_api(
                model, temperature, top_p, messages, functions
            )
        else:
            # LiteLLM path (legacy Chat Completions API)
            yield from self._get_completion_chat_api(
                model, temperature, top_p, messages, functions
            )

    def _get_completion_responses_api(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
    ) -> Generator[str, None, None]:
        """Handle completion using the new Responses API."""
        tool_call_id = name = arguments = ""
        
        # Convert messages to Responses API format
        instructions, input_items = self._messages_to_responses_api_format(messages)
        
        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "input": input_items if input_items else "",
        }
        
        # Add instructions if present
        if instructions:
            request_params["instructions"] = instructions
        
        # Add tool/function parameters if present
        if functions:
            request_params["tool_choice"] = "auto"
            request_params["tools"] = functions
            request_params["parallel_tool_calls"] = False
        
        # Call the Responses API stream method
        try:
            response_stream = completion(**request_params, **additional_kwargs)
            
            # Iterate through the stream events
            for event in response_stream:
                event_type = event.type
                
                # Handle text delta events (main content)
                if event_type == "response.output_text.delta":
                    yield event.delta
                
                # Handle function call argument deltas
                elif event_type == "response.function_call_arguments.delta":
                    arguments += event.delta
                    # Store the item_id as tool_call_id
                    tool_call_id = event.item_id
                
                # Handle function call arguments done (get function name)
                elif event_type == "response.function_call_arguments.done":
                    # We need to get the function name from the output item
                    pass
                
                # Handle output item added (includes function name)
                elif event_type == "response.output_item.added":
                    if hasattr(event, 'item') and event.item.get('type') == 'function_call':
                        name = event.item.get('name', '')
                        tool_call_id = event.item.get('id', '')
                
                # Handle output item done
                elif event_type == "response.output_item.done":
                    # Check if this was a function call that completed
                    if hasattr(event, 'item'):
                        item = event.item
                        if item.get('type') == 'function_call' and arguments:
                            # Execute the function call
                            yield from self.handle_function_call(
                                messages, tool_call_id, name, arguments
                            )
                            
                            # Recursive call for next completion
                            yield from self.get_completion(
                                model=model,
                                temperature=temperature,
                                top_p=top_p,
                                messages=messages,
                                functions=functions,
                                caching=False,
                            )
                            return
                
        except KeyboardInterrupt:
            if hasattr(response_stream, 'close'):
                response_stream.close()

    def _get_completion_chat_api(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
    ) -> Generator[str, None, None]:
        """Handle completion using the legacy Chat Completions API (for LiteLLM)."""
        tool_call_id = name = arguments = ""
        
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
