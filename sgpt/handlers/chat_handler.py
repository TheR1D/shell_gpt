import json
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

import tiktoken
import typer
from datetime import datetime
from click import BadArgumentUsage
from rich.console import Console
from rich.markdown import Markdown

from ..config import cfg
from ..role import DefaultRoles, SystemRole
from ..utils import option_callback
from .handler import Handler

DEBUGING = True
CHAT_CACHE_LENGTH = int(cfg.get("CHAT_CACHE_LENGTH"))
CHAT_CACHE_PATH = Path(cfg.get("CHAT_CACHE_PATH"))


class ChatSession:
    """
    This class is used as a decorator for OpenAI chat API requests.
    The ChatSession class caches chat messages and keeps track of the
    conversation history. It is designed to store cached messages
    in a specified directory and in JSON format.
    """

    def __init__(self, length: int, storage_path: Path, token_limit: int):
        """
        Initialize the ChatSession decorator.

        :param length: Integer, maximum number of cached messages to keep.
        """
        self.length = length
        self.storage_path = storage_path
        self.token_limit = token_limit
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        The Cache decorator.

        :param func: The chat function to cache.
        :return: Wrapped function with chat caching.
        """

        def wrapper(*args: Any, **kwargs: Any) -> Generator[str, None, None]:
            chat_id = kwargs.pop("chat_id", None)
            if not kwargs.get("messages"):
                return
            if not chat_id:
                yield from func(*args, **kwargs)
                return
            # Limit it!
            self._limit_tokens(chat_id, self.token_limit)
            previous_messages = self._read(chat_id)
            for message in kwargs["messages"]:
                previous_messages.append(message)
            kwargs["messages"] = previous_messages
            response_text = ""
            for word in func(*args, **kwargs):
                response_text += word
                yield word
            previous_messages.append({"role": "assistant", "content": response_text})
            self._write(kwargs["messages"], chat_id)

        return wrapper

    def _read(self, chat_id: str) -> List[Dict[str, str]]:
        file_path = self.storage_path / chat_id
        if not file_path.exists():
            return []
        parsed_cache = json.loads(file_path.read_text())
        return parsed_cache if isinstance(parsed_cache, list) else []

    def _write(self, messages: List[Dict[str, str]], chat_id: str) -> None:
        file_path = self.storage_path / chat_id

        json.dump(messages, file_path.open("w"))

    def _limit_tokens(self, chat_id, token_limit):
        while True:
            current_token_estimate = self._count_tokens(chat_id)
            if current_token_estimate > token_limit:
                messages = self._read(chat_id)
                if len(messages) < (1 + 2):
                    break
                # Remove 2nd and 3rd message (oldest question and answer)
                truncated_messages = messages[:1] + messages[3:]
                self._write(truncated_messages, chat_id)
            else:
                break

    def _count_tokens(self, chat_id: str) -> int:
        file_path = self.storage_path / chat_id
        if not file_path.exists():
            return 0
        parsed_cache = json.loads(file_path.read_text())
        messages = [
            message["content"] for message in parsed_cache if "content" in message
        ]
        text_to_encode = " ".join(messages)

        # tokenizer = tiktoken.encoding_for_model("gpt-4o")
        tokenizer = tiktoken.get_encoding("o200k_base")
        token_count = len(tokenizer.encode(text_to_encode))

        # Log the details to a file
        if DEBUGING:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = (
                f"{current_time}: "
                f"tokens {token_count} "
                f"messages {len(messages)}\n"
            )

            log_file_path = self.storage_path / f"{chat_id}_log.txt"
            with open(log_file_path, "a") as log_file:
                log_file.write(log_message)

        return token_count

    def invalidate(self, chat_id: str) -> None:
        file_path = self.storage_path / chat_id
        file_path.unlink(missing_ok=True)

    def get_messages(self, chat_id: str) -> List[str]:
        messages = self._read(chat_id)
        return [f"{message['role']}: {message['content']}" for message in messages]

    def exists(self, chat_id: Optional[str]) -> bool:
        return bool(chat_id and bool(self._read(chat_id)))

    def list(self) -> List[Path]:
        # Get all files in the folder.
        files = self.storage_path.glob("*")
        # Sort files by last modification time in ascending order.
        return sorted(files, key=lambda f: f.stat().st_mtime)


class ChatHandler(Handler):

    def __init__(
        self, chat_id: str, role: SystemRole, markdown: bool, token_limit: int
    ) -> None:
        super().__init__(role, markdown)
        self.chat_id = chat_id
        self.role = role
        self.chat_session = ChatSession(CHAT_CACHE_LENGTH, CHAT_CACHE_PATH, token_limit)

        # Apply the decorator to the instance method
        self.get_completion = self.chat_session(self.get_completion)

        if chat_id == "temp":
            # If the chat id is "temp", we don't want to save the chat session.
            self.chat_session.invalidate(chat_id)

        self.validate()

    @property
    def initiated(self) -> bool:
        return self.chat_session.exists(self.chat_id)

    @property
    def is_same_role(self) -> bool:
        # TODO: Should be optimized for REPL mode.
        return self.role.same_role(self.initial_message(self.chat_id))

    def initial_message(self, chat_id: str) -> str:
        chat_history = self.chat_session.get_messages(chat_id)
        return chat_history[0] if chat_history else ""

    @option_callback
    def list_ids(self, value: str) -> None:
        # Prints all existing chat IDs to the console.
        for chat_id in self.chat_session.list():
            typer.echo(chat_id)

    def show_messages(self, chat_id: str, markdown: bool) -> None:
        color = cfg.get("DEFAULT_COLOR")
        if "APPLY MARKDOWN" in self.initial_message(chat_id):
            theme = cfg.get("CODE_THEME")
            for message in self.chat_session.get_messages(chat_id) and markdown:
                if message.startswith("assistant:"):
                    Console().print(Markdown(message, code_theme=theme))
                else:
                    typer.secho(message, fg=color)
                typer.echo()
            return

        for index, message in enumerate(self.chat_session.get_messages(chat_id)):
            running_color = color if index % 2 == 0 else "green"
            typer.secho(message, fg=running_color)

    def validate(self) -> None:
        if self.initiated:
            chat_role_name = self.role.get_role_name(self.initial_message(self.chat_id))
            if not chat_role_name:
                raise BadArgumentUsage(
                    f'Could not determine chat role of "{self.chat_id}"'
                )
            if self.role.name == DefaultRoles.DEFAULT.value:
                # If user didn't pass chat mode, we will use the one that was used to initiate the chat.
                self.role = SystemRole.get(chat_role_name)
            else:
                if not self.is_same_role:
                    raise BadArgumentUsage(
                        f'Cant change chat role to "{self.role.name}" '
                        f'since it was initiated as "{chat_role_name}" chat.'
                    )

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        messages = []
        if not self.initiated:
            messages.append({"role": "system", "content": self.role.role})
        messages.append({"role": "user", "content": prompt})
        return messages

    def get_completion(self, **kwargs: Any) -> Generator[str, None, None]:
        yield from super().get_completion(**kwargs)

    def handle(self, **kwargs: Any) -> str:  # type: ignore[override]
        return super().handle(**kwargs, chat_id=self.chat_id)
