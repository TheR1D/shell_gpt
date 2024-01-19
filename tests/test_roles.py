import json
from pathlib import Path
from unittest.mock import patch

from sgpt.config import cfg
from sgpt.role import SystemRole

from .utils import app, cmd_args, comp_args, comp_chunks, runner


@patch("openai.resources.chat.Completions.create")
def test_role(completion):
    completion.return_value = comp_chunks('{"foo": "bar"}')
    path = Path(cfg.get("ROLE_STORAGE_PATH")) / "json_gen_test.json"
    path.unlink(missing_ok=True)
    args = {"--create-role": "json_gen_test"}
    stdin = "you are a JSON generator"
    result = runner.invoke(app, cmd_args(**args), input=stdin)
    completion.assert_not_called()
    assert result.exit_code == 0

    args = {"--list-roles": True}
    result = runner.invoke(app, cmd_args(**args))
    completion.assert_not_called()
    assert result.exit_code == 0
    assert "json_gen_test" in result.stdout

    args = {"--show-role": "json_gen_test"}
    result = runner.invoke(app, cmd_args(**args))
    completion.assert_not_called()
    assert result.exit_code == 0
    assert "you are a JSON generator" in result.stdout

    # Test with argument prompt.
    args = {
        "prompt": "generate foo, bar",
        "--role": "json_gen_test",
    }
    result = runner.invoke(app, cmd_args(**args))
    role = SystemRole.get("json_gen_test")
    completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    generated_json = json.loads(result.stdout)
    assert "foo" in generated_json

    # Test with stdin prompt.
    args = {"--role": "json_gen_test"}
    stdin = "generate foo, bar"
    result = runner.invoke(app, cmd_args(**args), input=stdin)
    completion.assert_called_with(**comp_args(role, stdin))
    assert result.exit_code == 0
    generated_json = json.loads(result.stdout)
    assert "foo" in generated_json
    path.unlink(missing_ok=True)
