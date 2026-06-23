import importlib.util
import sys
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple

from pydantic import BaseModel

from .config import cfg


class Function:
    def __init__(self, path: str):
        module = self._read(path)
        self._function = module.Function.execute
        self._openai_schema = module.Function.openai_schema()
        self._name = self._openai_schema["function"]["name"]

    @property
    def name(self) -> str:
        return self._name  # type: ignore

    @property
    def openai_schema(self) -> dict[str, Any]:
        return self._openai_schema  # type: ignore

    @property
    def execute(self) -> Callable[..., str]:
        return self._function  # type: ignore

    @classmethod
    def _read(cls, path: str) -> Any:
        module_name = path.replace("/", ".").rstrip(".py")
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)  # type: ignore
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore

        if not issubclass(module.Function, BaseModel):
            raise TypeError(
                f"Function {module_name} must be a subclass of pydantic.BaseModel"
            )
        if not hasattr(module.Function, "execute"):
            raise TypeError(
                f"Function {module_name} must have an 'execute' classmethod"
            )
        if not hasattr(module.Function, "openai_schema"):
            raise TypeError(
                f"Function {module_name} must have an 'openai_schema' classmethod"
            )

        return module


class _FunctionEntry(NamedTuple):
    function: Function
    execute: Callable[..., Any]
    params: set[str]
    has_kwargs: bool


functions_folder = Path(cfg.get("OPENAI_FUNCTIONS_PATH"))
functions_folder.mkdir(parents=True, exist_ok=True)

_functions_list = [Function(str(path)) for path in functions_folder.glob("*.py")]

_registry: dict[str, _FunctionEntry] = {}
for func in _functions_list:
    execute = func.execute
    sig = inspect.signature(execute)
    params = set(sig.parameters)
    has_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
    if func.name in _registry:
        raise ValueError(f"Duplicate function name: {func.name}")
    _registry[func.name] = _FunctionEntry(
        function=func,
        execute=execute,
        params=params,
        has_kwargs=has_kwargs,
    )


def get_function(name: str) -> Callable[..., Any]:
    entry = _registry.get(name)
    if entry is None:
        raise ValueError(f"Function {name} not found")

    def wrapper(**kwargs: Any) -> Any:
        if entry.has_kwargs:
            return entry.execute(**kwargs)
        filtered = {k: v for k, v in kwargs.items() if k in entry.params}
        return entry.execute(**filtered)

    return wrapper


def get_openai_schemas() -> List[Dict[str, Any]]:
    return [func.openai_schema for func in _functions_list]
