import requests
import json
from hashlib import md5
from pathlib import Path
from tempfile import gettempdir
from typing import List, Dict, Callable


class Cache:
    """
    Decorator class that adds caching functionality to a function.
    """

    CACHE_DIR = Path(gettempdir()) / "shell_gpt" / "cache"

    def __init__(self, length: int):
        """
        Initialize the Cache decorator.

        :param length: Integer, maximum number of cache files to keep.
        """
        self.length = length

    def __call__(self, func: Callable) -> Callable:
        """
        The Cache decorator.

        :param func: The function to cache.
        :return: Wrapped function with caching.
        """
        def wrapper(*args, **kwargs):
            if not kwargs.pop("caching", True):
                return func(*args, **kwargs)
            cache_dir = self.CACHE_DIR
            # Exclude self (ChatGPT) instance from hashing.
            cache_key = md5(json.dumps((args[1:], kwargs)).encode('utf-8')).hexdigest()
            cache_file = cache_dir / cache_key
            if cache_file.exists():
                return json.loads(cache_file.read_text())
            result = func(*args, **kwargs)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(result))
            self.__delete_oldest_files(self.length)
            return result
        return wrapper

    @classmethod
    def __delete_oldest_files(cls, max_files) -> None:
        """
        Class method to delete the oldest cached files in the CACHE_DIR folder.

        :param max_files: Integer, the maximum number of files to keep in the CACHE_DIR folder.
        """
        # Get all files in the folder.
        files = cls.CACHE_DIR.glob('*')
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

    CACHE_DIR = Path(gettempdir()) / "shell_gpt" / "chat_cache"
    CACHE_FILE_MAIN = CACHE_DIR / "main_cache.json"

    def __init__(self, length: int):
        """
        Initialize the ChatCache decorator.

        :param length: Integer, maximum number of cached messages to keep.
        """
        self.length = length

    def __call__(self, func: Callable) -> Callable:
        """
        The Cache decorator.

        :param func: The chat function to cache.
        :return: Wrapped function with chat caching.
        """
        def wrapper(*args, **kwargs):
            chat_id = kwargs.pop("chat_id", None)
            file_path = self.CACHE_DIR / chat_id if chat_id else self.CACHE_FILE_MAIN
            message = {"role": "user", "content": kwargs.pop("message")}
            kwargs["messages"] = self.read(file_path)
            kwargs["messages"].append(message)
            response_text = func(*args, **kwargs)
            kwargs["messages"].append({"role": "assistant", "content": response_text})
            self.write(kwargs["messages"], self.length, file_path)
            return response_text
        return wrapper

    @classmethod
    def read(cls, file_path: Path) -> List[Dict]:
        if not file_path.exists():
            return []
        parsed_cache = json.loads(file_path.read_text())
        if isinstance(parsed_cache, list):
            return parsed_cache
        return []

    @classmethod
    def write(cls, messages: List[Dict], length: int, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(messages[-length:], file_path.open("w"))

    @classmethod
    def invalidate(cls, chat_id: str):
        file_path = cls.CACHE_DIR / chat_id
        file_path.unlink()

    @classmethod
    def get_messages(cls, chat_id):
        messages = cls.read(cls.CACHE_DIR / chat_id)
        return [f"{message['role']}: {message['content']}" for message in messages]

    @classmethod
    def get_chats(cls):
        # Get all files in the folder.
        files = cls.CACHE_DIR.glob('*')
        # Sort files by last modification time in ascending order.
        return sorted(files, key=lambda f: f.stat().st_mtime)


class ChatGPT:
    """
    OpenAI ChatGPT API interface.
    """

    API_URL = "https://api.openai.com/v1/chat/completions"
    TEMP_FILE = Path(gettempdir()) / "shell_gpt_cache.json"
    chat_cache = ChatCache(length=50)
    cache = Cache(length=200)

    def __init__(self, api_key: str):
        """
        Initialize ChatGPT.

        :param api_key: OpenAI API key.
        """
        self.api_key = api_key

    @cache
    def __request(
        self,
        messages: List,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
    ) -> Dict:
        """
        Make request to OpenAI ChatGPT API, read more:
        https://platform.openai.com/docs/api-reference/chat

        :param messages: List of messages {"role": user or assistant, "content": message_string}
        :param model: String gpt-3.5-turbo or gpt-3.5-turbo-0301
        :param temperature: Float in 0.0 - 1.0 range.
        :param top_probability: Float in 0.0 - 1.0 range.
        :return: Response body JSON.
        """
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "top_p": top_probability,
        }
        response = requests.post(self.API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_completion(
        self,
        message: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1,
        caching: bool = True,
    ) -> str:
        """
        Generates single completion for prompt (message).

        :param message: String prompt to generate completion for.
        :param model: String gpt-3.5-turbo or gpt-3.5-turbo-0301.
        :param temperature: Float in 0.0 - 1.0 range.
        :param top_probability: Float in 0.0 - 1.0 range.
        :param caching: Boolean value to enable/disable caching.
        :return: String generated completion.
        """
        message = {"role": "user", "content": message}
        return self.__request(
            [message], model, temperature, top_probability, caching=caching
        )["choices"][0]["message"]["content"].strip()

    @chat_cache
    def get_chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-3.5-turbo",
        temperature: float = 1,
        top_probability: float = 1
    ) -> str:
        """
        Generate completion based on conversation. Note that this method
        should be used with ChatCache decorator, which will handle caching
        of messages. In this case messages parameter can be ignored, instead
        use just message argument. e.g: get_chat_completion(message="anything").

        :param messages: List of dialog messages, comes from caching decorator.
        :param model: String gpt-3.5-turbo or gpt-3.5-turbo-0301.
        :param temperature: Float in 0.0 - 1.0 range.
        :param top_probability: Float in 0.0 - 1.0 range.
        :return: String generated completion for last user message.
        """
        # It returns several leading/trailing whitespaces.
        return self.__request(
            messages, model, temperature, top_probability
        )["choices"][0]["message"]["content"].strip()
