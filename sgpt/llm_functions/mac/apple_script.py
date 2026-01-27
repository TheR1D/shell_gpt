import subprocess
from typing import Any, Dict

from pydantic import BaseModel, Field


class Function(BaseModel):
    """
    Executes Apple Script on macOS and returns the output (result).
    Can be used for actions like: draft (prepare) an email, show calendar events, create a note.
    """

    apple_script: str = Field(
        default=...,
        example='tell application "Finder" to get the name of every disk',
        description="Apple Script to execute.",
    )  # type: ignore

    @classmethod
    def execute(cls, apple_script):
        script_command = ["osascript", "-e", apple_script]
        try:
            process = subprocess.Popen(
                script_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            output, _ = process.communicate()
            output = output.decode("utf-8").strip()
            return f"Output: {output}"
        except Exception as e:
            return f"Error: {e}"

    @classmethod
    def openai_schema(cls) -> Dict[str, Any]:
        """Generate OpenAI function schema from Pydantic model."""
        schema = cls.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": "execute_apple_script",
                "description": cls.__doc__.strip() if cls.__doc__ else "",
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }
