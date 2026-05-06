"""Configuration loading for the Acunetix MCP server.

Settings are read from, in order:
1. ``.env`` loaded by python-dotenv
2. ``config.yaml`` or the path in ``ACUNETIX_MCP_CONFIG``
3. Environment variables, which always win over the config file

Validation is explicit and happens when the Acunetix client is used, so MCP
tool discovery works even before credentials are configured.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

try:  # PyYAML is declared as a runtime dependency.
    import yaml
except Exception:  # pragma: no cover - only used if dependency resolution broke.
    yaml = None


TRUE_VALUES = {"1", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off"}


def mask_secret(value: str, secret: str | None = None) -> str:
    """Return ``value`` with known secret material redacted."""
    if not value:
        return value
    masked = value
    if secret:
        masked = masked.replace(secret, "***REDACTED***")
    return masked


def _parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def _parse_int(value: Any, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _parse_float(value: Any, default: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _parse_csv(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(item.strip() for item in str(value).split(",") if item.strip())


def _nested_get(data: Mapping[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _env_or_config(env_name: str, data: Mapping[str, Any], *paths: str) -> Any:
    if env_name in os.environ:
        return os.environ[env_name]
    for path in paths:
        value = _nested_get(data, path)
        if value is not None:
            return value
    return None


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        raise ValueError("PyYAML is required to read config.yaml")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping")
    return loaded


def normalize_acunetix_base_url(base_url: str) -> str:
    """Normalize user-provided Acunetix URL to the REST API base path."""
    stripped = (base_url or "").strip().rstrip("/")
    if not stripped:
        return ""
    parts = urlsplit(stripped)
    if not parts.scheme or not parts.netloc:
        return stripped
    path = parts.path.rstrip("/")
    if not path.endswith("/api/v1"):
        path = f"{path}/api/v1" if path else "/api/v1"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


@dataclass(slots=True)
class Settings:
    acunetix_base_url: str = ""
    acunetix_api_key: str = ""
    acunetix_verify_ssl: bool = False
    request_timeout_seconds: float = 30.0

    mcp_transport: str = "stdio"
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080

    read_only: bool = True
    require_confirmation: bool = True
    allowed_targets: tuple[str, ...] = ()
    max_concurrent_scan_starts: int = 1

    audit_log_path: str | None = None
    log_level: str = "INFO"
    config_file: str | None = None

    @property
    def api_base_url(self) -> str:
        return normalize_acunetix_base_url(self.acunetix_base_url)

    def validate(self) -> None:
        if not self.acunetix_base_url:
            raise ValueError("ACUNETIX_BASE_URL is not set.")
        if not self.api_base_url:
            raise ValueError("ACUNETIX_BASE_URL is invalid.")
        if not self.acunetix_api_key:
            raise ValueError("ACUNETIX_API_KEY is not set.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("ACUNETIX_TIMEOUT_SECONDS must be greater than zero.")
        if self.max_concurrent_scan_starts < 1:
            raise ValueError("ACUNETIX_MAX_CONCURRENT_SCAN_STARTS must be at least 1.")


class Config(Settings):
    """Backward-compatible alias used by older tests/imports."""


def load_settings() -> Settings:
    """Load settings from dotenv, YAML config, and environment variables."""
    load_dotenv()

    config_file = os.getenv("ACUNETIX_MCP_CONFIG", "config.yaml")
    config_path = Path(config_file)
    data = _load_yaml_config(config_path)

    verify_ssl_value = os.getenv("ACUNETIX_VERIFY_SSL")
    if verify_ssl_value is None:
        verify_ssl_value = _env_or_config(
            "VERIFY_SSL",
            data,
            "acunetix.verify_ssl",
            "verify_ssl",
        )

    transport = _env_or_config("MCP_TRANSPORT", data, "mcp.transport") or "stdio"

    return Settings(
        acunetix_base_url=(
            _env_or_config("ACUNETIX_BASE_URL", data, "acunetix.base_url", "base_url") or ""
        ),
        acunetix_api_key=(
            _env_or_config("ACUNETIX_API_KEY", data, "acunetix.api_key", "api_key") or ""
        ),
        acunetix_verify_ssl=_parse_bool(verify_ssl_value, default=False),
        request_timeout_seconds=_parse_float(
            _env_or_config(
                "ACUNETIX_TIMEOUT_SECONDS",
                data,
                "acunetix.timeout_seconds",
                "timeout_seconds",
            ),
            default=30.0,
        ),
        mcp_transport=str(transport).strip().lower(),
        mcp_server_host=str(
            _env_or_config("MCP_SERVER_HOST", data, "mcp.host") or "0.0.0.0"
        ),
        mcp_server_port=_parse_int(
            _env_or_config("MCP_SERVER_PORT", data, "mcp.port"),
            default=8080,
        ),
        read_only=_parse_bool(
            _env_or_config("ACUNETIX_READ_ONLY", data, "policy.read_only"),
            default=True,
        ),
        require_confirmation=_parse_bool(
            _env_or_config(
                "ACUNETIX_REQUIRE_CONFIRMATION",
                data,
                "policy.require_confirmation",
            ),
            default=True,
        ),
        allowed_targets=_parse_csv(
            _env_or_config(
                "ACUNETIX_TARGET_ALLOWLIST",
                data,
                "policy.allowed_targets",
            )
        ),
        max_concurrent_scan_starts=_parse_int(
            _env_or_config(
                "ACUNETIX_MAX_CONCURRENT_SCAN_STARTS",
                data,
                "policy.max_concurrent_scan_starts",
            ),
            default=1,
        ),
        audit_log_path=(
            _env_or_config("ACUNETIX_AUDIT_LOG", data, "audit.log_path") or None
        ),
        log_level=str(
            _env_or_config("LOG_LEVEL", data, "logging.level") or "INFO"
        ).upper(),
        config_file=str(config_path),
    )


config = load_settings()
