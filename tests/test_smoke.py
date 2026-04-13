"""Smoke tests — no Acunetix instance required."""

import os
import asyncio
import pytest

# Set env vars BEFORE importing any acunetix_mcp modules.
# In production the client sets these lazily; here we just need them
# so config.validate() (called lazily on first HTTP call) would pass.
os.environ.setdefault("ACUNETIX_BASE_URL", "https://127.0.0.1:3443/api/v1")
os.environ.setdefault("ACUNETIX_API_KEY", "test-key-for-smoke-tests")

from acunetix_mcp.server import mcp, create_server  # noqa: E402
from acunetix_mcp.config import Config               # noqa: E402


EXPECTED_TOOLS = {
    # Targets
    "acunetix__list_targets",
    "acunetix__get_target",
    "acunetix__add_target",
    # Scans
    "acunetix__list_scans",
    "acunetix__start_scan",
    "acunetix__get_scan_status",
    "acunetix__abort_scan",
    "acunetix__get_scan_results",
    "acunetix__list_scanning_profiles",
    # Vulnerabilities
    "acunetix__list_vulnerabilities",
    "acunetix__get_vulnerability",
    "acunetix__update_vulnerability_status",
    "acunetix__list_vulnerability_types",
    # Reports
    "acunetix__list_report_templates",
    "acunetix__generate_report",
    "acunetix__list_reports",
    "acunetix__get_report",
    # Results
    "acunetix__get_scan_result",
    "acunetix__get_scan_statistics",
}

EXPECTED_TOOL_COUNT = len(EXPECTED_TOOLS)  # 19


class TestServerCreation:
    """Server initialises correctly without a live Acunetix instance."""

    def test_server_instance_exists(self):
        assert mcp is not None

    def test_server_name(self):
        assert mcp.name == "acunetix-mcp"

    @pytest.mark.asyncio
    async def test_tool_count(self):
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert len(tools) == EXPECTED_TOOL_COUNT, (
            f"Expected {EXPECTED_TOOL_COUNT} tools, got {len(tools)}.\n"
            f"Extra:   {names - EXPECTED_TOOLS}\n"
            f"Missing: {EXPECTED_TOOLS - names}"
        )

    @pytest.mark.asyncio
    async def test_all_tools_have_acunetix_prefix(self):
        tools = await mcp.list_tools()
        bad = [t.name for t in tools if not t.name.startswith("acunetix__")]
        assert not bad, f"Tools without namespace prefix: {bad}"

    @pytest.mark.asyncio
    async def test_all_expected_tools_registered(self):
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}
        missing = EXPECTED_TOOLS - tool_names
        assert not missing, f"Missing tools: {missing}"

    @pytest.mark.asyncio
    async def test_all_tools_have_description(self):
        """Every tool must have a non-empty docstring for LLM discovery."""
        tools = await mcp.list_tools()
        no_desc = [t.name for t in tools if not (t.description or "").strip()]
        assert not no_desc, f"Tools without description: {no_desc}"


class TestConfig:
    """Configuration loading and validation."""

    def test_config_has_required_fields(self):
        cfg = Config()
        assert hasattr(cfg, "ACUNETIX_BASE_URL")
        assert hasattr(cfg, "ACUNETIX_API_KEY")
        assert hasattr(cfg, "VERIFY_SSL")
        assert hasattr(cfg, "MCP_SERVER_HOST")
        assert hasattr(cfg, "MCP_SERVER_PORT")

    def test_config_validate_missing_url(self):
        cfg = Config()
        cfg.ACUNETIX_BASE_URL = ""
        cfg.ACUNETIX_API_KEY = "some-key"
        with pytest.raises(ValueError, match="ACUNETIX_BASE_URL"):
            cfg.validate()

    def test_config_validate_missing_key(self):
        cfg = Config()
        cfg.ACUNETIX_BASE_URL = "https://example.com/api/v1"
        cfg.ACUNETIX_API_KEY = ""
        with pytest.raises(ValueError, match="ACUNETIX_API_KEY"):
            cfg.validate()

    def test_config_validate_success(self):
        cfg = Config()
        cfg.ACUNETIX_BASE_URL = "https://example.com/api/v1"
        cfg.ACUNETIX_API_KEY = "valid-key"
        cfg.validate()  # must not raise

    def test_import_does_not_crash_without_env(self, monkeypatch):
        """Config module must not raise on import even if env vars are missing."""
        # Temporarily remove vars from the Config class-level values
        cfg = Config()
        cfg.ACUNETIX_BASE_URL = ""
        cfg.ACUNETIX_API_KEY = ""
        # validate() should raise, but object creation must not
        with pytest.raises(ValueError):
            cfg.validate()
        # The module-level singleton must still exist
        from acunetix_mcp.config import config as module_config
        assert module_config is not None
