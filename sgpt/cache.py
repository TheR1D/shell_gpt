import json
from hashlib import md5
from pathlib import Path
from typing import List, Dict, Callable, Optional


class Cache:
    """
    Decorator class that adds caching functionality to a function.
    """

    def __init__(self, length: int, cache_path: Path) -> None:
        """
        Initialize the Cache decorator.

        :param length: Integer, maximum number of cache files to keep.
        """
        self.length = length
        self.cache_path = cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def __call__(self, func: Callable) -> Callable:
        """
        The Cache decorator.

        :param func: The function to cache.
        :return: Wrapped function with caching.
        """

        def wrapper(*args, **kwargs):
            # Exclude self instance from hashing.
            cache_key = md5(json.dumps((args[1:], kwargs)).encode("utf-8")).hexdigest()
            cache_file = self.cache_path / cache_key
            # TODO: Fix caching for chat, should hash last user message, (not entire history).
            if kwargs.pop("caching", True) and cache_file.exists():
                yield cache_file.read_text()
                return
            result = ""
            for i in func(*args, **kwargs):
                result += i
                yield i
            cache_file.write_text(result)
            self._delete_oldest_files(self.length)

        return wrapper

    def _delete_oldest_files(self, max_files) -> None:
        """
        Class method to delete the oldest cached files in the CACHE_DIR folder.

        :param max_files: Integer, the maximum number of files to keep in the CACHE_DIR folder.
        """
        # Get all files in the folder.
        files = self.cache_path.glob("*")
        # Sort files by last modification time in ascending order.
        files = sorted(files, key=lambda f: f.stat().st_mtime)
        # Delete the oldest files if the number of files exceeds the limit.
        if len(files) > max_files:
            num_files_to_delete = len(files) - max_files
            for i in range(num_files_to_delete):
                files[i].unlink()


class ChatCache:
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
        json.dump(messages[-self.length:], file_path.open("w"))

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
