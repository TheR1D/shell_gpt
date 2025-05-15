import importlib.util
import sys
from abc import ABCMeta
from pathlib import Path
from typing import Any, Callable, Dict, List

from .config import cfg


class Function:
    def __init__(self, path: str):
        module = self._read(path)
        self._function = module.Function.execute
        self._openai_schema = module.Function.openai_schema
        self._name = self._openai_schema["name"]

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


def get_openai_schemas() -> List[Dict[str, Any]]:
    transformed_schemas = []
    for function in functions:
        # Deep copy to avoid modifying the original schema in Function object,
        # though in this specific case it might not be strictly necessary
        # as get_openai_schemas is usually called once per run.
        # However, it's safer if the underlying Function objects are reused.
        import copy
        raw_parameters = copy.deepcopy(function.openai_schema.get("parameters", {}))

        if "properties" in raw_parameters:
            for _param_name, param_details in raw_parameters["properties"].items():
                if "descriptions" in param_details:
                    param_details["description"] = param_details.pop("descriptions")
                # Ensure 'type' exists, Gemini might be strict
                if "type" not in param_details and "anyOf" not in param_details and "allOf" not in param_details and "oneOf" not in param_details:
                     # Default to string if no type is specified, though Pydantic usually infers this.
                     # This is a defensive measure.
                    param_details["type"] = "string"


        schema = {
            "type": "function",
            "function": {
                "name": function.openai_schema["name"],
                "description": function.openai_schema.get("description", ""),
                "parameters": raw_parameters,
            },
        }
        transformed_schemas.append(schema)
    return transformed_schemas
