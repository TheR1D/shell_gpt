import json
from pathlib import Path
from typing import List, Dict, Optional, Callable, Generator

import typer
from click import BadArgumentUsage

from sgpt import OpenAIClient, config, make_prompt
from sgpt.utils import CompletionModes
from sgpt.handlers.handler import Handler

CHAT_CACHE_LENGTH = int(config.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(config.get("CHAT_CACHE_PATH"))


class ChatSession:
    """
    This class is used as a decorator for OpenAI chat API requests.
    The ChatCache class caches chat messages and keeps track of the
    conversation history. It is designed to store cached messages
    in a specified directory and in JSON format.
    """

    def __init__(self, length: int, storage_path: Path):
        """
        Initialize the ChatCache decorator.

        :param length: Integer, maximum number of cached messages to keep.
        """
        self.length = length
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def __call__(self, func: Callable) -> Callable:
        """
        The Cache decorator.

        :param func: The chat function to cache.
        :return: Wrapped function with chat caching.
        """

        def wrapper(*args, **kwargs):
            chat_id = kwargs.pop("chat_id", None)
            messages = kwargs["messages"]
            if not chat_id:
                yield from func(*args, **kwargs)
                return
            old_messages = self._read(chat_id)
            for message in messages:
                old_messages.append(message)
            kwargs["messages"] = old_messages
            response_text = ""
            for word in func(*args, **kwargs):
                response_text += word
                yield word
            old_messages.append({"role": "assistant", "content": response_text})
            self._write(kwargs["messages"], chat_id)

        return wrapper

    def _read(self, chat_id: str) -> List[Dict]:
        file_path = self.storage_path / chat_id
        if not file_path.exists():
            return []
        parsed_cache = json.loads(file_path.read_text())
        return parsed_cache if isinstance(parsed_cache, list) else []

    def _write(self, messages: List[Dict], chat_id: str):
        file_path = self.storage_path / chat_id
        json.dump(messages[-self.length :], file_path.open("w"))

    def invalidate(self, chat_id: str):
        file_path = self.storage_path / chat_id
        file_path.unlink()

    def get_messages(self, chat_id):
        messages = self._read(chat_id)
        return [f"{message['role']}: {message['content']}" for message in messages]

    def exists(self, chat_id: Optional[str]) -> bool:
        return chat_id and bool(self._read(chat_id))

    def list(self):
        # Get all files in the folder.
        files = self.storage_path.glob("*")
        # Sort files by last modification time in ascending order.
        return sorted(files, key=lambda f: f.stat().st_mtime)


class ChatHandler(Handler):
    chat_session = ChatSession(CHAT_CACHE_LENGTH, CHAT_CACHE_PATH)

    def __init__(  # pylint: disable=too-many-arguments
        self,
        client: OpenAIClient,
        chat_id: str,
        shell: bool = False,
        code: bool = False,
        model: str = "gpt-3.5-turbo",
    ) -> None:
        super().__init__(client)
        self.chat_id = chat_id
        self.client = client
        self.mode = CompletionModes.get_mode(shell, code)
        self.model = model

        chat_history = self.chat_session.get_messages(self.chat_id)
        self.is_shell_chat = chat_history and chat_history[0].endswith("###\nCommand:")
        self.is_code_chat = chat_history and chat_history[0].endswith("###\nCode:")
        self.is_default_chat = chat_history and chat_history[0].endswith("###")

        self.validate()

    @classmethod
    def list_ids(cls, value) -> None:
        if not value:
            return
        # Prints all existing chat IDs to the console.
        for chat_id in cls.chat_session.list():
            typer.echo(chat_id)
        raise typer.Exit()

    @classmethod
    def show_messages(cls, chat_id: str) -> None:
        if not chat_id:
            return
        # Prints all messages from a specified chat ID to the console.
        for index, message in enumerate(cls.chat_session.get_messages(chat_id)):
            message = message.replace("\nCommand:", "").replace("\nCode:", "")
            color = "cyan" if index % 2 == 0 else "green"
            typer.secho(message, fg=color)
        raise typer.Exit()

    def validate(self) -> None:
        if self.initiated:
            if self.is_shell_chat and self.mode == CompletionModes.CODE:
                raise BadArgumentUsage(
                    f'Chat session "{self.chat_id}" was initiated as shell assistant, '
                    "and can be used with --shell only"
                )
            if self.is_code_chat and self.mode == CompletionModes.SHELL:
                raise BadArgumentUsage(
                    f'Chat "{self.chat_id}" was initiated as code assistant, '
                    "and can be used with --code only"
                )
            if self.is_default_chat and self.mode != CompletionModes.NORMAL:
                raise BadArgumentUsage(
                    f'Chat "{self.chat_id}" was initiated as default assistant, '
                    "and can't be used with --shell or --code"
                )
            # If user didn't pass chat mode, we will use the one that was used to initiate the chat.
            if self.mode == CompletionModes.NORMAL:
                if self.is_shell_chat:
                    self.mode = CompletionModes.SHELL
                elif self.is_code_chat:
                    self.mode = CompletionModes.CODE

    @property
    def initiated(self) -> bool:
        return self.chat_session.exists(self.chat_id)

    def make_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        if self.initiated:
            if self.is_shell_chat:
                prompt += "\nCommand:"
            elif self.is_code_chat:
                prompt += "\nCode:"
            return prompt
        return make_prompt.initial(
            prompt,
            self.mode == CompletionModes.SHELL,
            self.mode == CompletionModes.CODE,
        )

    @chat_session
    def get_completion(  # pylint: disable=arguments-differ
        self,
        **kwargs,
    ) -> Generator:
        yield from super().get_completion(**kwargs)
