import json
from hashlib import md5
from pathlib import Path
from typing import Any, Callable, Generator, no_type_check


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

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        The Cache decorator.

        :param func: The function to cache.
        :return: Wrapped function with caching.
        """

        def wrapper(*args: Any, **kwargs: Any) -> Generator[str, None, None]:
            key = md5(json.dumps((args[1:], kwargs)).encode("utf-8")).hexdigest()
            file = self.cache_path / key
            if kwargs.pop("caching") and file.exists():
                yield file.read_text()
                return
            result = ""
            for i in func(*args, **kwargs):
                result += i
                yield i
            if "@FunctionCall" not in result:
                file.write_text(result)
            self._delete_oldest_files(self.length)  # type: ignore

        return wrapper

    @no_type_check
    def _delete_oldest_files(self, max_files: int) -> None:
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
