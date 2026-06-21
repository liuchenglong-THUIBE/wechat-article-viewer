import json

from wechat_reader.core.config import Config


def test_config_uses_env_config_path(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"llm_api_key": "env-config-key"}),
        encoding="utf-8",
    )

    monkeypatch.setenv("WECHAT_READER_CONFIG_PATH", str(config_path))

    config = Config()

    assert config.config_path == config_path
    assert config.get("llm_api_key") == "env-config-key"
