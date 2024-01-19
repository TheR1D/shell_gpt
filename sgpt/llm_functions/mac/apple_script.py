import subprocess

from instructor import OpenAISchema
from pydantic import Field


class Function(OpenAISchema):
    """
    Executes Apple Script on macOS and returns the output (result).
    Can be used for actions like: draft (prepare) an email, show calendar events, create a note.
    """

    apple_script: str = Field(
        ...,
        example='tell application "Finder" to get the name of every disk',
        descriptions="Apple Script to execute.",
    )

    class Config:
        title = "execute_apple_script"

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
