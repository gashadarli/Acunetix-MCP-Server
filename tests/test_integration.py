"""Integration tests — requires a running Acunetix instance.

Run with:
    pytest tests/test_integration.py -v

Requires .env with valid ACUNETIX_BASE_URL and ACUNETIX_API_KEY.
All tests are read-only (GET only) to avoid modifying scanner state.
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

HAS_API_KEY = bool(
    os.getenv("ACUNETIX_API_KEY")
    and os.getenv("ACUNETIX_API_KEY") != "test-key-for-smoke-tests"
)
SKIP = "ACUNETIX_API_KEY not set or is placeholder value"

pytestmark = pytest.mark.skipif(not HAS_API_KEY, reason=SKIP)

from acunetix_mcp.client import AcunetixClient  # noqa: E402


@pytest.fixture
def client():
    return AcunetixClient()


class TestTargets:
    @pytest.mark.asyncio
    async def test_list_targets(self, client):
        result = await client.get("/targets", params={"l": 5})
        assert result["success"] is True
        assert "data" in result

    @pytest.mark.asyncio
    async def test_list_targets_with_search(self, client):
        result = await client.get("/targets", params={"l": 5, "q": "text:a"})
        assert result["success"] is True


class TestScans:
    @pytest.mark.asyncio
    async def test_list_scans(self, client):
        result = await client.get("/scans", params={"l": 5})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_scanning_profiles(self, client):
        result = await client.get("/scanning_profiles")
        assert result["success"] is True


class TestVulnerabilities:
    @pytest.mark.asyncio
    async def test_list_vulnerabilities(self, client):
        result = await client.get("/vulnerabilities", params={"l": 5})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_vulnerability_types(self, client):
        result = await client.get("/vulnerability_types", params={"l": 5})
        assert result["success"] is True


class TestReports:
    @pytest.mark.asyncio
    async def test_list_report_templates(self, client):
        result = await client.get("/report_templates")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_reports(self, client):
        result = await client.get("/reports", params={"l": 5})
        assert result["success"] is True
