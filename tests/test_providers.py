import json

import pytest
from click import UsageError

from sgpt import providers
from sgpt.config import cfg


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SGPT_PROVIDERS_PATH", str(tmp_path / "providers.json"))
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.delenv("SGPT_PROVIDER", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    # Config.get() takes one argument, so pytest's setitem helper cannot patch it.
    snapshot = dict(cfg)
    cfg["API_BASE_URL"] = "default"
    try:
        yield
    finally:
        cfg.clear()
        cfg.update(snapshot)


def make_provider(name="deepseek", preset="deepseek", **kwargs):
    preset_data = providers.PRESETS[preset]
    return providers.Provider(
        name=name,
        preset=preset,
        base_url=kwargs.get("base_url", preset_data.base_url),
        model=kwargs.get("model", preset_data.model),
        api_key_env=kwargs.get("api_key_env", preset_data.api_key_env),
    )


def test_presets_are_usable():
    for name, preset in providers.PRESETS.items():
        assert preset.base_url.startswith(("https://", "http://")), name
        assert not preset.base_url.endswith(" "), name
        assert preset.model, name
        if preset.api_key_env is not None:
            assert preset.api_key_env == preset.api_key_env.upper(), name


def test_name_pattern():
    assert providers.NAME_RE.match("deepseek")
    assert providers.NAME_RE.match("ollama-local")
    assert not providers.NAME_RE.match("DeepSeek")
    assert not providers.NAME_RE.match("-leading")
    assert not providers.NAME_RE.match("a" * 33)


def test_save_and_load_roundtrip():
    providers.save(make_provider())
    stored = json.loads(providers.path().read_text(encoding="utf-8"))
    assert stored["version"] == 1
    assert stored["active"] == "deepseek"
    assert providers.profiles()["deepseek"].model == "deepseek-flash"


def test_no_secret_is_written(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-secret-value-that-must-not-leak")
    providers.save(make_provider())
    text = providers.path().read_text(encoding="utf-8")
    assert "sk-secret-value-that-must-not-leak" not in text
    assert "DEEPSEEK_API_KEY" in text


def test_corrupt_file_is_backed_up_not_fatal():
    file = providers.path()
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("{not json", encoding="utf-8")
    assert providers.profiles() == {}
    assert file.with_name(file.name + ".bak").exists()


def test_failed_write_keeps_previous_file(monkeypatch):
    providers.save(make_provider())
    before = providers.path().read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(providers, "_replace", boom)
    with pytest.raises(OSError):
        providers.save(make_provider(name="groq", preset="groq"))

    assert providers.path().read_text(encoding="utf-8") == before
    leftovers = [
        p for p in providers.path().parent.iterdir() if p.name.startswith(".providers-")
    ]
    assert leftovers == []


def test_skips_unreadable_entries():
    providers.path().parent.mkdir(parents=True, exist_ok=True)
    providers.path().write_text(
        json.dumps(
            {
                "providers": {
                    "good": {"base_url": "https://x/v1", "model": "m"},
                    "bad": {"model": "m"},
                    "worse": "nope",
                }
            }
        ),
        encoding="utf-8",
    )
    assert list(providers.profiles()) == ["good"]


def test_resolve_precedence(monkeypatch):
    providers.save(make_provider(name="deepseek"))
    providers.save(make_provider(name="groq", preset="groq"))

    assert providers.resolve().name == "groq"  # last saved is active

    monkeypatch.setenv("SGPT_PROVIDER", "deepseek")
    assert providers.resolve().name == "deepseek"
    assert providers.resolve("groq").name == "groq"  # flag beats env


def test_unknown_provider_lists_known(monkeypatch):
    providers.save(make_provider())
    with pytest.raises(UsageError) as error:
        providers.resolve("nope")
    assert "deepseek" in str(error.value)


def test_legacy_fallback_without_profiles(monkeypatch):
    cfg["DEFAULT_MODEL"] = "legacy-model"
    resolved = providers.resolve()
    assert resolved.name == "default"
    assert resolved.model == "legacy-model"
    assert resolved.base_url == ""
    assert resolved.api_key() == "test_api_key"


def test_legacy_api_base_url_overrides_profile(monkeypatch):
    providers.save(make_provider())
    cfg["API_BASE_URL"] = "https://gateway.local/v1"
    assert providers.resolve().base_url == "https://gateway.local/v1"


def test_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "abc123")
    provider = make_provider()
    assert provider.api_key() == "abc123"
    assert provider.key_present is True

    monkeypatch.delenv("DEEPSEEK_API_KEY")
    assert provider.api_key() is None
    assert provider.key_present is False


def test_ollama_has_placeholder_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = make_provider(name="ollama", preset="ollama")
    assert provider.api_key() == "ollama"
    assert provider.key_present is True


def test_remove_active_reassigns_or_clears():
    providers.save(make_provider(name="deepseek"))
    providers.save(make_provider(name="groq", preset="groq"))
    providers.remove("groq")
    assert providers.active_name() == "deepseek"

    providers.remove("deepseek")
    assert providers.active_name() is None
    assert providers.profiles() == {}


def test_rows_mark_active(monkeypatch):
    providers.save(make_provider(name="deepseek"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "abc123")
    rows = providers.rows()
    assert rows == [
        (
            "deepseek",
            "deepseek",
            "deepseek-flash",
            "https://api.deepseek.com",
            "DEEPSEEK_API_KEY",
            "ok",
            "yes",
        )
    ]


def test_stored_key_is_used_and_labelled():
    provider = providers.Provider(
        name="deepseek",
        preset="deepseek",
        base_url=providers.PRESETS["deepseek"].base_url,
        model=providers.PRESETS["deepseek"].model,
        api_key_env="DEEPSEEK_API_KEY",
        api_key_value="sk-stored",
    )
    providers.save(provider)
    loaded = providers.profiles()["deepseek"]
    assert loaded.api_key() == "sk-stored"
    assert (
        json.loads(providers.path().read_text(encoding="utf-8"))["providers"][
            "deepseek"
        ]["api_key"]
        == "sk-stored"
    )


def test_env_var_wins_over_stored_key(monkeypatch):
    provider = providers.Provider(
        name="deepseek",
        preset="deepseek",
        base_url=providers.PRESETS["deepseek"].base_url,
        model=providers.PRESETS["deepseek"].model,
        api_key_env="DEEPSEEK_API_KEY",
        api_key_value="sk-stored",
    )
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env")
    assert provider.api_key() == "sk-env"
