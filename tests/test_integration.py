"""Integration tests for Acunetix MCP Server - requires running Acunetix instance.

Run with: pytest tests/test_integration.py -v
Requires: .env with valid ACUNETIX_BASE_URL and ACUNETIX_API_KEY

These tests connect to the real Acunetix API. They only perform
read operations (GET) to avoid modifying state.
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# Skip all tests if no API key configured
SKIP_REASON = "ACUNETIX_API_KEY not set or set to test value"
HAS_API_KEY = (
    os.getenv("ACUNETIX_API_KEY", "")
    and os.getenv("ACUNETIX_API_KEY") != "test-key-for-smoke-tests"
)

pytestmark = pytest.mark.skipif(not HAS_API_KEY, reason=SKIP_REASON)

from acunetix_mcp.client import AcunetixClient
from acunetix_mcp.config import config


@pytest.fixture
def client():
    return AcunetixClient()


class TestTargets:
    @pytest.mark.asyncio
    async def test_get_targets(self, client):
        result = await client.get("/targets", params={"l": 5})
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_targets_csv_export(self, client):
        result = await client.get("/targets/cvs_export")
        assert result["success"] is True


class TestScans:
    @pytest.mark.asyncio
    async def test_get_scans(self, client):
        result = await client.get("/scans", params={"l": 5})
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_scanning_profiles(self, client):
        result = await client.get("/scanning_profiles")
        assert result["success"] is True


class TestVulnerabilities:
    @pytest.mark.asyncio
    async def test_get_vulnerabilities(self, client):
        result = await client.get("/vulnerabilities", params={"l": 5})
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_vulnerability_types(self, client):
        result = await client.get("/vulnerability_types", params={"l": 5})
        assert result["success"] is True


class TestReports:
    @pytest.mark.asyncio
    async def test_get_report_templates(self, client):
        result = await client.get("/report_templates")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_reports(self, client):
        result = await client.get("/reports", params={"l": 5})
        assert result["success"] is True


class TestUsers:
    @pytest.mark.asyncio
    async def test_get_users(self, client):
        result = await client.get("/users", params={"l": 5})
        assert result["success"] is True


class TestGroups:
    @pytest.mark.asyncio
    async def test_get_target_groups(self, client):
        result = await client.get("/target_groups")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_user_groups(self, client):
        result = await client.get("/user_groups")
        assert result["success"] is True


class TestWorkers:
    @pytest.mark.asyncio
    async def test_get_workers(self, client):
        result = await client.get("/workers")
        assert result["success"] is True


class TestIssueTrackers:
    @pytest.mark.asyncio
    async def test_get_issue_trackers(self, client):
        result = await client.get("/issue_trackers")
        assert result["success"] is True


class TestWafs:
    @pytest.mark.asyncio
    async def test_get_wafs(self, client):
        result = await client.get("/wafs")
        assert result["success"] is True


class TestRoles:
    @pytest.mark.asyncio
    async def test_get_roles(self, client):
        result = await client.get("/roles")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_permissions(self, client):
        result = await client.get("/roles/permissions")
        assert result["success"] is True


class TestExcludedHours:
    @pytest.mark.asyncio
    async def test_get_excluded_hours(self, client):
        result = await client.get("/excluded_hours_profiles")
        assert result["success"] is True
