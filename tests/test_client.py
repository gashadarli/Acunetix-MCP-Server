import httpx
import pytest

from acunetix_mcp.client import AcunetixClient
from acunetix_mcp.config import Settings


def _settings(api_key: str = "secret-test-key") -> Settings:
    return Settings(
        acunetix_base_url="https://acunetix.local/",
        acunetix_api_key=api_key,
        acunetix_verify_ssl=False,
    )


@pytest.mark.asyncio
async def test_client_sends_auth_header_and_normalizes_base_url():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["x_auth"] = request.headers.get("X-Auth")
        return httpx.Response(200, json={"targets": []})

    client = AcunetixClient(
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )

    result = await client.get("/targets", params={"l": 5})

    assert result["success"] is True
    assert seen["url"] == "https://acunetix.local/api/v1/targets?l=5"
    assert seen["x_auth"] == "secret-test-key"


@pytest.mark.asyncio
async def test_client_masks_secret_in_api_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "bad secret-test-key"})

    client = AcunetixClient(
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )

    result = await client.get("/targets")

    assert result["success"] is False
    assert "secret-test-key" not in str(result)
    assert "***REDACTED***" in str(result)


@pytest.mark.asyncio
async def test_client_returns_clear_timeout_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    client = AcunetixClient(
        settings=_settings(),
        transport=httpx.MockTransport(handler),
    )

    result = await client.get("/targets")

    assert result["success"] is False
    assert result["error"]["type"] == "ReadTimeout"
