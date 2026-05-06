import json

import pytest

from acunetix_mcp.server import create_server


EXPECTED_PROMPTS = {
    "acunetix_inventory_summary",
    "acunetix_scan_status_report",
    "acunetix_vulnerability_triage",
    "acunetix_safe_scan_start_checklist",
}

EXPECTED_RESOURCES = {
    "acunetix://tool-coverage",
    "acunetix://policy",
    "acunetix://openapi-summary",
    "acunetix://configuration-template",
}


@pytest.mark.asyncio
async def test_lobehub_prompts_are_registered():
    mcp = create_server()

    prompts = await mcp.list_prompts()

    assert EXPECTED_PROMPTS.issubset({prompt.name for prompt in prompts})
    for prompt in prompts:
        if prompt.name in EXPECTED_PROMPTS:
            assert prompt.description


@pytest.mark.asyncio
async def test_lobehub_resources_are_registered():
    mcp = create_server()

    resources = await mcp.list_resources()

    assert EXPECTED_RESOURCES.issubset({str(resource.uri) for resource in resources})
    for resource in resources:
        if str(resource.uri) in EXPECTED_RESOURCES:
            assert resource.description


@pytest.mark.asyncio
async def test_tool_coverage_resource_is_safe_json():
    mcp = create_server()

    content = await mcp.read_resource("acunetix://tool-coverage")
    payload = json.loads(content.contents[0].content)

    assert payload["coverage"] == "full"
    assert payload["documented_operations"] == 161
    assert payload["missing_operations"] == 0


@pytest.mark.asyncio
async def test_policy_resource_does_not_expose_secret(monkeypatch):
    monkeypatch.setenv("ACUNETIX_API_KEY", "super-secret-value")
    monkeypatch.setenv("ACUNETIX_MCP_CONFIG", "missing-test-config.yaml")
    mcp = create_server()

    content = await mcp.read_resource("acunetix://policy")
    text = content.contents[0].content

    assert "super-secret-value" not in text
    assert json.loads(text)["api_key_configured"] is True
