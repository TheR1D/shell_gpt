import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_legacy_function_schema_does_not_crash_import(tmp_path):
    home = tmp_path / "home"
    functions_path = home / ".config" / "shell_gpt" / "functions"
    functions_path.mkdir(parents=True)
    (functions_path / "legacy.py").write_text(
        textwrap.dedent(
            """
            from typing import Any, ClassVar
            from pydantic import BaseModel


            class Function(BaseModel):
                openai_schema: ClassVar[dict[str, Any]] = {
                    "function": {"name": "legacy"}
                }

                @classmethod
                def execute(cls):
                    return "ok"
            """
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["OPENAI_API_KEY"] = "test-key"

    result = subprocess.run(
        [sys.executable, "-m", "sgpt", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
