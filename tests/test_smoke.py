"""Smoke tests for Acunetix MCP Server - no Acunetix instance required."""

import os
import asyncio
import pytest

# Ensure env vars are set so config.validate() doesn't fail during import
os.environ.setdefault("ACUNETIX_BASE_URL", "https://127.0.0.1:3443/api/v1")
os.environ.setdefault("ACUNETIX_API_KEY", "test-key-for-smoke-tests")

from acunetix_mcp.server import mcp, create_server
from acunetix_mcp.config import Config


class TestServerCreation:
    """Test that the MCP server initializes correctly."""

    def test_server_instance_exists(self):
        assert mcp is not None

    def test_server_name(self):
        assert mcp.name == "Acunetix MCP Server"

    @pytest.mark.asyncio
    async def test_tool_count(self):
        tools = await mcp.list_tools()
        assert len(tools) == 161, f"Expected 161 tools, got {len(tools)}"

    @pytest.mark.asyncio
    async def test_all_expected_tools_registered(self):
        tools = await mcp.list_tools()
        tool_names = {t.name for t in tools}

        # Core tools that must exist
        expected = {
            # Targets
            "get_targets", "add_target", "get_target", "update_target",
            "remove_target", "configure_target",
            # Scans
            "get_scans", "schedule_scan", "get_scan", "abort_scan",
            "resume_scan", "trigger_scan",
            # Vulnerabilities
            "get_vulnerabilities", "get_vulnerability_details",
            "set_vulnerability_status",
            # Reports
            "get_reports", "generate_new_report", "get_report_templates",
            "download_report",
            # New tools
            "upload_login_sequence", "download_login_sequence",
            "upload_client_certificate", "upload_import_file",
            "download_sensor", "get_issue_tracker_issue_types_by_query",
        }

        missing = expected - tool_names
        assert not missing, f"Missing tools: {missing}"


class TestConfig:
    """Test configuration loading."""

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
        cfg.validate()  # Should not raise
