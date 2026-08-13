import os
import subprocess
import sys


def test_llm_defaults_from_config(tmp_path):
    config_folder = tmp_path / ".config" / "shell_gpt"
    config_folder.mkdir(parents=True)
    config_path = config_folder / ".sgptrc"
    config_path.write_text(
        "OPENAI_API_KEY=test\n"
        "DEFAULT_TEMPERATURE=0.7\n"
        "DEFAULT_TOP_P=0.8\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["USERPROFILE"] = str(tmp_path)
    env.pop("DEFAULT_TEMPERATURE", None)
    env.pop("DEFAULT_TOP_P", None)

    result = subprocess.run(
        [sys.executable, "-m", "sgpt", "--help"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--temperature" in result.stdout
    assert "default: 0.7" in result.stdout
    assert "--top-p" in result.stdout
    assert "default: 0.8" in result.stdout
