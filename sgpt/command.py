from pathlib import Path
from click import UsageError
import json


class Command:
    def __init__(self, command_path: Path):
        self.command_path = command_path
        self.command_path.mkdir(parents=True, exist_ok=True)

    def get_last_command(self) -> tuple[str, str]:
        """
        get the last command and output from the command path
        """
        last_command_file = self.command_path / "last_command.json"
        if not last_command_file.exists():
            raise UsageError("No last command and output found.")
        with open(last_command_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            command = data.get("command", "")
            output = data.get("output", "")
            return command, output

    def set_last_command(self, command: str, output: str) -> None:
        """
        set the last command and output to the command path
        """
        last_command_file = self.command_path / "last_command.json"
        with open(last_command_file, "w", encoding="utf-8") as file:
            data = {"command": command, "output": output}
            json.dump(data, file, ensure_ascii=False)
