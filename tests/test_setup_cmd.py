import pytest
from typer.testing import CliRunner

from sgpt import providers
from sgpt.config import cfg
from sgpt.setup_cmd import app as setup_app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SGPT_PROVIDERS_PATH", str(tmp_path / "providers.json"))
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.delenv("SGPT_PROVIDER", raising=False)
    snapshot = dict(cfg)
    cfg["API_BASE_URL"] = "default"
    try:
        yield
    finally:
        cfg.clear()
        cfg.update(snapshot)


def test_list_without_profiles():
    result = runner.invoke(setup_app, ["list"])
    assert result.exit_code == 0, result
    assert "No providers saved" in result.output


def test_list_marks_active(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "abc")
    providers.save(
        providers.Provider(
            name="deepseek",
            preset="deepseek",
            base_url=providers.PRESETS["deepseek"].base_url,
            model=providers.PRESETS["deepseek"].model,
            api_key_env="DEEPSEEK_API_KEY",
        )
    )
    result = runner.invoke(setup_app, ["list"])
    assert result.exit_code == 0, result
    assert "deepseek" in result.output
    assert "key var" in result.output
    assert "active: deepseek" in result.output


def test_handler_follows_active_provider(monkeypatch):
    """The client settings must come from the provider active at call time."""
    monkeypatch.setenv("GROQ_API_KEY", "abc")
    providers.save(
        providers.Provider(
            name="groq",
            preset="groq",
            base_url=providers.PRESETS["groq"].base_url,
            model=providers.PRESETS["groq"].model,
            api_key_env="GROQ_API_KEY",
        )
    )
    from sgpt.handlers.handler import _provider_kwargs

    kwargs = _provider_kwargs()
    assert kwargs["base_url"].rstrip("/") == "https://api.groq.com/openai/v1"
    assert kwargs["api_key"] == "abc"


def test_missing_key_is_a_usage_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    providers.save(
        providers.Provider(
            name="groq",
            preset="groq",
            base_url=providers.PRESETS["groq"].base_url,
            model=providers.PRESETS["groq"].model,
            api_key_env="GROQ_API_KEY",
        )
    )
    from click import UsageError

    from sgpt.handlers.handler import _provider_kwargs

    with pytest.raises(UsageError, match="GROQ_API_KEY"):
        _provider_kwargs()


def save(name: str, preset: str, key_env: str | None = "TEST_KEY") -> None:
    preset_data = providers.PRESETS[preset]
    providers.save(
        providers.Provider(
            name=name,
            preset=preset,
            base_url=preset_data.base_url,
            model=preset_data.model,
            api_key_env=key_env,
        )
    )


def test_use_switches_active():
    save("deepseek", "deepseek")
    save("groq", "groq")
    result = runner.invoke(setup_app, ["use", "deepseek"])
    assert result.exit_code == 0, result
    assert providers.active_name() == "deepseek"
    assert "deepseek" in result.output


def test_use_unknown_provider_fails():
    result = runner.invoke(setup_app, ["use", "nope"])
    assert result.exit_code == 1
    assert "No such provider" in result.output


def test_remove_reassigns_active():
    save("deepseek", "deepseek")
    save("groq", "groq")
    result = runner.invoke(setup_app, ["remove", "groq"], input="y\n")
    assert result.exit_code == 0, result
    assert providers.active_name() == "deepseek"
    assert "deepseek" in result.output


def test_probe_reports_latency(monkeypatch):
    save("groq", "groq", "GROQ_API_KEY")
    monkeypatch.setenv("GROQ_API_KEY", "abc")
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return object()

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    result = runner.invoke(setup_app, ["test", "groq"])
    assert result.exit_code == 0, result
    assert "OK groq" in result.output and " ms" in result.output
    assert calls[0]["model"] == providers.PRESETS["groq"].model
    assert calls[0]["max_tokens"] == 1


def test_probe_without_key_is_a_usage_error(monkeypatch):
    save("groq", "groq", "GROQ_API_KEY")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = runner.invoke(setup_app, ["test", "groq"])
    assert result.exit_code == 2
    assert "GROQ_API_KEY is not set" in result.output


def test_wizard_saves_profile(monkeypatch):
    monkeypatch.setattr("sgpt.setup_cmd._is_tty", lambda: True)
    monkeypatch.setattr("sgpt.setup_cmd._ask_preset", lambda: "deepseek")
    inputs = "\n\nsk-test-key-0123456789abcdef\nn\n"
    result = runner.invoke(setup_app, [], input=inputs)
    assert result.exit_code == 0, result
    saved = providers.profiles()["deepseek"]
    assert saved.base_url == providers.PRESETS["deepseek"].base_url
    assert saved.api_key_env == "DEEPSEEK_API_KEY"
    assert saved.api_key_value == "sk-test-key-0123456789abcdef"
    assert providers.active_name() == "deepseek"


def test_wizard_requires_a_tty():
    result = runner.invoke(setup_app, [])
    assert result.exit_code == 2
    assert "No interactive terminal" in result.output


def test_setup_flag_opens_the_wizard():
    """`sgpt --setup` is an alias for `sgpt setup`."""
    from .utils import app as cli
    from .utils import runner as cli_runner

    result = cli_runner.invoke(cli, ["--setup"])
    assert result.exit_code == 2  # no TTY under CliRunner
    assert "No interactive terminal" in result.output


def test_use_without_name_uses_picker(monkeypatch):
    save("deepseek", "deepseek")
    monkeypatch.setattr("sgpt.setup_cmd._ask_profile", lambda title: "deepseek")
    result = runner.invoke(setup_app, ["use"])
    assert result.exit_code == 0, result
    assert providers.active_name() == "deepseek"


def test_use_without_name_and_cancel(monkeypatch):
    save("deepseek", "deepseek")
    monkeypatch.setattr("sgpt.setup_cmd._ask_profile", lambda title: None)
    result = runner.invoke(setup_app, ["use"])
    assert result.exit_code == 1
    assert "Cancelled" in result.output


def test_dialog_failure_falls_back_to_typing(monkeypatch):
    from prompt_toolkit import shortcuts

    def no_console(**kwargs):
        raise RuntimeError("no console")

    monkeypatch.setattr(shortcuts, "radiolist_dialog", no_console)
    monkeypatch.setattr("typer.prompt", lambda *a, **k: "groq")
    from sgpt.setup_cmd import _ask_preset

    assert _ask_preset() == "groq"


def test_wizard_accepts_a_pasted_key(monkeypatch):
    """A key typed in the wizard is stored, so 'test' works without env vars."""
    from sgpt.setup_cmd import _ask_credential

    monkeypatch.setattr(
        "typer.prompt", lambda *args, **kwargs: "sk-1234567890abcdef1234567890abcdef"
    )
    env, value = _ask_credential("DEEPSEEK_API_KEY")
    assert value == "sk-1234567890abcdef1234567890abcdef"
    assert env == "DEEPSEEK_API_KEY"


def test_dialog_enter_selects_immediately():
    """The picker must not need a second Enter for an OK button."""
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from sgpt.setup_cmd import _build_dialog

    with create_pipe_input() as pipe:
        pipe.send_text("\x1b[B\r")  # down, enter
        app = _build_dialog(
            "Provider",
            [("a", "first"), ("b", "second")],
            input=pipe,
            output=DummyOutput(),
        )
        assert app.run() == "b"


def test_dialog_escape_cancels():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from sgpt.setup_cmd import _build_dialog

    with create_pipe_input() as pipe:
        pipe.send_text("\x1b")  # escape
        app = _build_dialog(
            "Provider", [("a", "first")], input=pipe, output=DummyOutput()
        )
        assert app.run() is None


def test_dialog_wraps_around():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from sgpt.setup_cmd import _build_dialog

    with create_pipe_input() as pipe:
        pipe.send_text("\x1b[A\r")  # up from the first entry wraps to the last
        app = _build_dialog(
            "Provider",
            [("a", "first"), ("b", "second")],
            input=pipe,
            output=DummyOutput(),
        )
        assert app.run() == "b"


def test_remove_needs_confirmation():
    save("deepseek", "deepseek")
    result = runner.invoke(setup_app, ["remove", "deepseek"], input="n\n")
    assert result.exit_code == 1
    assert "Cancelled" in result.output
    assert "deepseek" in providers.profiles()


def test_use_without_profiles_is_a_clean_error():
    result = runner.invoke(setup_app, ["use"])
    assert result.exit_code == 1
    assert "Error:" in result.output and "No providers saved" in result.output
