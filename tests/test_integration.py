"""Read-only integration tests for a real Acunetix instance.

Run explicitly with:
    pytest tests/test_integration.py -v

The tests are skipped unless ACUNETIX_BASE_URL and ACUNETIX_API_KEY are set.
They never start scans or modify Acunetix state.
"""

import os

import pytest
from dotenv import load_dotenv

from acunetix_mcp.client import AcunetixClient


load_dotenv()

HAS_REAL_CONFIG = bool(os.getenv("ACUNETIX_BASE_URL") and os.getenv("ACUNETIX_API_KEY"))
pytestmark = pytest.mark.skipif(
    not HAS_REAL_CONFIG,
    reason="ACUNETIX_BASE_URL and ACUNETIX_API_KEY are required",
)


@pytest.fixture
def client():
    return AcunetixClient()


@pytest.mark.asyncio
async def test_acunetix_health(client):
    result = await client.health()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_list_target_groups(client):
    result = await client.get("/target_groups", params={"l": 5})
    assert result["success"] is True
    assert "data" in result


@pytest.mark.asyncio
async def test_list_targets(client):
    result = await client.get("/targets", params={"l": 5})
    assert result["success"] is True
    assert "data" in result


@pytest.mark.asyncio
async def test_list_scans(client):
    result = await client.get("/scans", params={"l": 5})
    assert result["success"] is True
    assert "data" in result
