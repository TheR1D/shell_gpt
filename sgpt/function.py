import importlib.util
import sys
from abc import ABCMeta
from pathlib import Path
from typing import Any, Callable

from .config import cfg


class Function:
    def __init__(self, path: str):
        module = self._read(path)
        self._function = module.Function.execute
        self._openai_schema = module.Function.openai_schema
        self._name = self._openai_schema["name"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def openai_schema(self) -> dict[str, Any]:
        return self._openai_schema

    @property
    def execute(self) -> Callable[..., str]:
        return self._function

    @classmethod
    def _read(cls, path: str) -> Any:
        module_name = path.replace("/", ".").rstrip(".py")
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not isinstance(module.Function, ABCMeta):
            raise TypeError(
                f"Function {module_name} must be a subclass of pydantic.BaseModel"
            )
        if not hasattr(module.Function, "execute"):
            raise TypeError(
                f"Function {module_name} must have a 'execute' static method"
            )

        return module


functions_folder = Path(cfg.get("OPENAI_FUNCTIONS_PATH"))
functions_folder.mkdir(parents=True, exist_ok=True)
functions = [Function(str(path)) for path in functions_folder.glob("*.py")]


def get_function(name: str) -> Callable[..., Any]:
    for function in functions:
        if function.name == name:
            return function.execute
    raise ValueError(f"Function {name} not found")


def get_openai_schemas() -> [dict[str, Any]]:
    return [function.openai_schema for function in functions]
