from sgpt.config import DEFAULT_CONFIG, POTENTIAL_PATH_KEYS, Config


def test_openai_api_key_string(tmp_path):
    temp_config_path = tmp_path / "temp_file"
    fake_api_key = "fake-api-key"
    cfg = Config(temp_config_path, **{**DEFAULT_CONFIG, "OPENAI_API_KEY": fake_api_key})
    assert cfg["OPENAI_API_KEY"] == fake_api_key


def test_openai_api_key_path(tmp_path):
    api_key_path = tmp_path / "api_key_file"
    temp_config_path = tmp_path / "temp_file"
    fake_api_key = "fake-api-key"

    api_key_path.write_text(fake_api_key)
    temp_config_path.write_text(f"OPENAI_API_KEY={api_key_path}")

    cfg = Config(temp_config_path, **DEFAULT_CONFIG, OPENAI_API_KEY=api_key_path)
    assert cfg["OPENAI_API_KEY"] == fake_api_key


def test_POTENTIAL_PATH_KEYS_includes_OPENAI_API_KEY():
    assert "OPENAI_API_KEY" in POTENTIAL_PATH_KEYS
