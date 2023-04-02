from pathlib import Path
from typing import Dict

import typer
from sgpt import config
from sgpt.utils import option_callback


class SystemRole:
    storage = Path(config.get("ROLE_STORAGE_PATH"))

    def __init__(self, name: str, role: str) -> None:
        self.storage.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.role = role

    @classmethod
    def get(cls, name: str) -> "SystemRole":
        file_path = cls.storage / f"{name}.txt"
        print(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'Role "{name}" not found.')
        return cls(name, role=file_path.read_text())

    @classmethod
    def create(cls, name: str) -> None:
        if not name:
            return
        role = typer.prompt("Enter role description")
        role = cls(name, role)
        role.save()
        raise typer.Exit()

    @classmethod
    @option_callback
    def list(cls) -> None:
        if not cls.storage.exists():
            return
        # Get all files in the folder.
        files = cls.storage.glob("*")
        # Sort files by last modification time in ascending order.
        for path in sorted(files, key=lambda f: f.stat().st_mtime):
            typer.echo(path)

    @classmethod
    @option_callback
    def show(cls, name: str):
        typer.echo(cls.get(name).role)

    @property
    def exists(self) -> bool:
        return self.file_path.exists()

    @property
    def system_message(self) -> Dict[str, str]:
        return {"role": "system", "content": self.role}

    @property
    def file_path(self) -> Path:
        return self.storage / f"{self.name}.txt"

    def save(self) -> None:
        if self.exists:
            typer.confirm(
                f'Role "{self.name}" already exists, overwrite it?',
                abort=True,
            )
        self.file_path.write_text(self.role, encoding="utf-8")


    # if __name__ == "__main__":
    #     check_and_setup_default_roles()
    #     # This is just for testing.
    #     save_role(
    #         "test",
    #         "Hello, You are a role testing AI."
    #         "Please always respond with a more enthusiastic test response, "
    #         "and all context provided.",
    #         executable_returns=False,
    #         prompt_structure="Hello, {prompt}!",
    #         conversation_lead_in=[
    #             {"role": "user", "content": "{shell} and os {os} Test Test"},
    #             {"role": "assistant", "content": "{shell} and os {os} Test Test Test!"},
    #         ],
    #         echo=True,
    #     )
    #     _list_roles(echo=True)
    #     _show_role("test", echo=True)
    #
    #     _show_role("code", echo=True)

