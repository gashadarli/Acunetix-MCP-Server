from acunetix_mcp.config import load_settings, normalize_acunetix_base_url


def test_normalize_base_url_adds_api_path():
    assert normalize_acunetix_base_url("https://10.0.244.136/") == (
        "https://10.0.244.136/api/v1"
    )


def test_normalize_base_url_preserves_api_path():
    assert normalize_acunetix_base_url("https://example.com/api/v1/") == (
        "https://example.com/api/v1"
    )


def test_load_settings_env_overrides_yaml(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
acunetix:
  base_url: "https://from-file.local/"
  api_key: "from-file"
  verify_ssl: true
policy:
  read_only: false
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("ACUNETIX_MCP_CONFIG", str(config_file))
    monkeypatch.setenv("ACUNETIX_BASE_URL", "https://from-env.local/")
    monkeypatch.setenv("ACUNETIX_API_KEY", "from-env")
    monkeypatch.setenv("ACUNETIX_VERIFY_SSL", "false")

    settings = load_settings()

    assert settings.api_base_url == "https://from-env.local/api/v1"
    assert settings.acunetix_api_key == "from-env"
    assert settings.acunetix_verify_ssl is False
    assert settings.read_only is False


def test_load_settings_defaults_to_safe_read_only(tmp_path, monkeypatch):
    monkeypatch.setenv("ACUNETIX_MCP_CONFIG", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("ACUNETIX_BASE_URL", raising=False)
    monkeypatch.delenv("ACUNETIX_API_KEY", raising=False)
    monkeypatch.delenv("ACUNETIX_READ_ONLY", raising=False)

    settings = load_settings()

    assert settings.read_only is True
    assert settings.require_confirmation is True
    assert settings.mcp_server_port == 8080
