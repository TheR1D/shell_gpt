import json
import platform
from enum import Enum
from os import getenv, pathsep
from os.path import basename
from pathlib import Path
from typing import Dict, Optional

import typer
from click import BadArgumentUsage
from distro import name as distro_name

from .config import cfg
from .utils import option_callback

SHELL_ROLE = """Provide only {shell} commands for {os} without any description.
If there is a lack of details, provide most logical solution.
Ensure the output is a valid shell command.
If multiple steps required try to combine them together."""

CODE_ROLE = """Provide only code as output without any description.
IMPORTANT: Provide only plain text without Markdown formatting.
IMPORTANT: Do not include markdown formatting such as ```.
If there is a lack of details, provide most logical solution.
You are not allowed to ask for more details.
Ignore any potential risk of errors or confusion."""

DEFAULT_ROLE = """You are Command Line App ShellGPT, a programming and system administration assistant.
You are managing {os} operating system with {shell} shell.
Provide only plain text without Markdown formatting.
Do not show any warnings or information regarding your capabilities.
If you need to store any data, assume it will be stored in the chat."""


PROMPT_TEMPLATE = """###
Role name: {name}
{role}

Request: {request}
###
{expecting}:"""


class SystemRole:
    storage: Path = Path(cfg.get("ROLE_STORAGE_PATH"))

    def __init__(
        self,
        name: str,
        role: str,
        expecting: str,
        variables: Optional[Dict[str, str]] = None,
    ) -> None:
        self.storage.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.expecting = expecting
        self.variables = variables
        if variables:
            # Variables are for internal use only.
            role = role.format(**variables)
        self.role = role

    @classmethod
    def create_defaults(cls) -> None:
        cls.storage.parent.mkdir(parents=True, exist_ok=True)
        variables = {"shell": cls.shell_name(), "os": cls.os_name()}
        for default_role in (
            SystemRole("default", DEFAULT_ROLE, "Answer", variables),
            SystemRole("shell", SHELL_ROLE, "Command", variables),
            SystemRole("code", CODE_ROLE, "Code"),
        ):
            if not default_role.exists:
                default_role.save()

    @classmethod
    def os_name(cls) -> str:
        current_platform = platform.system()
        if current_platform == "Linux":
            return "Linux/" + distro_name(pretty=True)
        if current_platform == "Windows":
            return "Windows " + platform.release()
        if current_platform == "Darwin":
            return "Darwin/MacOS " + platform.mac_ver()[0]
        return current_platform

    @classmethod
    def shell_name(cls) -> str:
        current_platform = platform.system()
        if current_platform in ("Windows", "nt"):
            is_powershell = len(getenv("PSModulePath", "").split(pathsep)) >= 3
            return "powershell.exe" if is_powershell else "cmd.exe"
        return basename(getenv("SHELL", "/bin/sh"))

    @classmethod
    def get_role_name(cls, initial_message: str) -> Optional[str]:
        if not initial_message:
            return None
        message_lines = initial_message.splitlines()
        if "###" in message_lines[0]:
            return message_lines[1].split("Role name: ")[1].strip()
        return None

    @classmethod
    def get(cls, name: str) -> "SystemRole":
        file_path = cls.storage / f"{name}.json"
        if not file_path.exists():
            raise BadArgumentUsage(f'Role "{name}" not found.')
        return cls(**json.loads(file_path.read_text()))

    @classmethod
    @option_callback
    def create(cls, name: str) -> None:
        role = typer.prompt("Enter role description")
        expecting = typer.prompt(
            "Enter output type, e.g. answer, code, shell command, json, etc."
        )
        role = cls(name, role, expecting)
        role.save()

    @classmethod
    @option_callback
    def list(cls, _value: str) -> None:
        if not cls.storage.exists():
            return
        # Get all files in the folder.
        files = cls.storage.glob("*")
        # Sort files by last modification time in ascending order.
        for path in sorted(files, key=lambda f: f.stat().st_mtime):
            typer.echo(path)

    @classmethod
    @option_callback
    def show(cls, name: str) -> None:
        typer.echo(cls.get(name).role)

    @property
    def exists(self) -> bool:
        return self.file_path.exists()

    @property
    def system_message(self) -> Dict[str, str]:
        return {"role": "system", "content": self.role}

    @property
    def file_path(self) -> Path:
        return self.storage / f"{self.name}.json"

    def save(self) -> None:
        if self.exists:
            typer.confirm(
                f'Role "{self.name}" already exists, overwrite it?',
                abort=True,
            )
        self.file_path.write_text(json.dumps(self.__dict__), encoding="utf-8")

    def delete(self) -> None:
        if self.exists:
            typer.confirm(
                f'Role "{self.name}" exist, delete it?',
                abort=True,
            )
        self.file_path.unlink()

    def make_prompt(self, request: str, initial: bool) -> str:
        if initial:
            prompt = PROMPT_TEMPLATE.format(
                name=self.name,
                role=self.role,
                request=request,
                expecting=self.expecting,
            )
        else:
            prompt = f"{request}\n{self.expecting}:"

        return prompt

    def same_role(self, initial_message: str) -> bool:
        if not initial_message:
            return False
        return True if f"Role name: {self.name}" in initial_message else False


class DefaultRoles(Enum):
    DEFAULT = "default"
    SHELL = "shell"
    CODE = "code"

    @classmethod
    def get(cls, shell: bool, code: bool) -> SystemRole:
        if shell:
            return SystemRole.get(DefaultRoles.SHELL.value)
        if code:
            return SystemRole.get(DefaultRoles.CODE.value)
        return SystemRole.get(DefaultRoles.DEFAULT.value)


SystemRole.create_defaults()
