import json
from pathlib import Path
from typing import Any, Dict, Generator, List

import typer
from openai import OpenAI
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from ..cache import Cache
from ..config import cfg
from ..function import get_function
from ..role import DefaultRoles, SystemRole

cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))


class Handler:
    def __init__(self, role: SystemRole) -> None:
        self.client = OpenAI(
            base_url=cfg.get("OPENAI_BASE_URL"),
            api_key=cfg.get("OPENAI_API_KEY"),
            timeout=int(cfg.get("REQUEST_TIMEOUT")),
        )
        self.role = role
        self.disable_stream = cfg.get("DISABLE_STREAMING") == "true"
        self.show_functions_output = cfg.get("SHOW_FUNCTIONS_OUTPUT") == "true"
        self.color = cfg.get("DEFAULT_COLOR")
        self.theme_name = cfg.get("CODE_THEME")

    def _handle_with_markdown(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(prompt.strip())
        full_completion = ""
        with Live(
            Markdown(markup="", code_theme=self.theme_name),
            console=Console(),
        ) as live:
            if self.disable_stream:
                live.update(
                    Markdown(markup="Loading...\r", code_theme=self.theme_name),
                    refresh=True,
                )
            for word in self.get_completion(messages=messages, **kwargs):
                full_completion += word
                live.update(
                    Markdown(markup=full_completion, code_theme=self.theme_name),
                    refresh=not self.disable_stream,
                )
        return full_completion

    def _handle_with_plain_text(self, prompt: str, **kwargs: Any) -> str:
        messages = self.make_messages(prompt.strip())
        full_completion = ""
        if self.disable_stream:
            typer.echo("Loading...\r", nl=False)
        for word in self.get_completion(messages=messages, **kwargs):
            typer.secho(word, fg=self.color, bold=True, nl=False)
            full_completion += word
        # Overwrite "loading..."
        typer.echo("\033[K" if not self.disable_stream else "")
        return full_completion

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def handle_function_call(
        self,
        messages: List[dict[str, str]],
        name: str,
        arguments: str,
    ) -> Generator[str, None, None]:
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "function_call": {"name": name, "arguments": arguments},  # type: ignore
            }
        )

        if messages and messages[-1]["role"] == "assistant":
            yield "\n"

        dict_args = json.loads(arguments)
        joined_args = ", ".join(f'{k}="{v}"' for k, v in dict_args.items())
        yield f"> @FunctionCall `{name}({joined_args})` \n\n"
        result = get_function(name)(**dict_args)
        if self.show_functions_output:
            yield f"```text\n{result}\n```\n"
        messages.append({"role": "function", "content": result, "name": name})

    # TODO: Fix MyPy typing errors. This modules is excluded from MyPy checks.
    @cache
    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        func_call = {"name": None, "arguments": ""}

        is_shell_role = self.role.name == DefaultRoles.SHELL.value
        is_code_role = self.role.name == DefaultRoles.CODE.value
        is_dsc_shell_role = self.role.name == DefaultRoles.DESCRIBE_SHELL.value
        if is_shell_role or is_code_role or is_dsc_shell_role:
            kwargs["functions"] = None

        if self.disable_stream:
            completion = self.client.chat.completions.create(**kwargs)
            message = completion.choices[0].message
            if completion.choices[0].finish_reason == "function_call":
                name, arguments = (
                    message.function_call.name,
                    message.function_call.arguments,
                )
                yield from self.handle_function_call(
                    kwargs["messages"], name, arguments
                )
                yield from self.get_completion(**kwargs, caching=False)
            yield message.content or ""
            return

        for chunk in self.client.chat.completions.create(**kwargs, stream=True):
            delta = chunk.choices[0].delta
            if delta.function_call:
                if delta.function_call.name:
                    func_call["name"] = delta.function_call.name
                if delta.function_call.arguments:
                    func_call["arguments"] += delta.function_call.arguments
            if chunk.choices[0].finish_reason == "function_call":
                name, arguments = func_call["name"], func_call["arguments"]
                yield from self.handle_function_call(
                    kwargs["messages"], name, arguments
                )
                yield from self.get_completion(**kwargs, caching=False)
                return

            yield delta.content or ""

    def handle(self, prompt: str, **kwargs: Any) -> str:
        default = DefaultRoles.DEFAULT.value
        shell_descriptor = DefaultRoles.DESCRIBE_SHELL.value
        if self.role.name == default or self.role.name == shell_descriptor:
            return self._handle_with_markdown(prompt, **kwargs)
        return self._handle_with_plain_text(prompt, **kwargs)
