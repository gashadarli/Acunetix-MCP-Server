import pytest

from acunetix_mcp.server import create_server
from acunetix_mcp.tools.openapi_coverage import build_operation_catalog, coverage_report


CORE_TOOLS = {
    "acunetix_health",
    "list_targets",
    "get_target",
    "list_target_groups",
    "get_target_group",
    "list_scans",
    "get_scan_status",
    "list_scanning_profiles",
    "list_vulnerabilities",
    "get_vulnerability",
    "update_vulnerability_status",
    "list_report_templates",
    "list_reports",
    "get_report",
    "create_target",
    "start_scan",
    "stop_scan",
    "generate_report",
}


class FakeAcunetix:
    def __init__(self):
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append(("get", path, params, None))
        return {"success": True, "data": {"path": path, "params": params}}

    async def post(self, path, body=None, params=None):
        self.calls.append(("post", path, params, body))
        return {"success": True, "data": {"path": path, "body": body}}

    async def put(self, path, body=None):
        self.calls.append(("put", path, None, body))
        return {"success": True, "data": {"path": path, "body": body}}

    async def patch(self, path, body=None):
        self.calls.append(("patch", path, None, body))
        return {"success": True, "data": {"path": path, "body": body}}

    async def delete(self, path, body=None):
        self.calls.append(("delete", path, None, body))
        return {"success": True, "data": {"path": path, "body": body}}


@pytest.mark.asyncio
async def test_core_and_full_coverage_tools_registered():
    mcp = create_server()

    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}
    report = coverage_report(tool_names)

    assert CORE_TOOLS.issubset(tool_names)
    assert report["documented_operations"] == 161
    assert report["implemented_operations"] == 161
    assert report["missing_operations"] == 0


@pytest.mark.asyncio
async def test_read_only_get_operations_are_registered():
    mcp = create_server()

    tool_names = {tool.name for tool in await mcp.list_tools()}
    get_operation_tools = {
        operation.tool_name
        for operation in build_operation_catalog()
        if operation.method == "get"
    }

    assert get_operation_tools.issubset(tool_names)
    assert {"list_users", "list_wafs", "download_report"}.issubset(tool_names)


@pytest.mark.asyncio
async def test_tools_have_descriptions_and_input_schemas():
    mcp = create_server()

    tools = await mcp.list_tools()

    for tool in tools:
        assert tool.description
        assert tool.parameters["type"] == "object"


@pytest.mark.asyncio
async def test_mutating_tools_expose_confirmation_argument():
    mcp = create_server()

    tools = {tool.name: tool for tool in await mcp.list_tools()}
    mutating_tool_names = {
        operation.tool_name
        for operation in build_operation_catalog()
        if operation.method in {"post", "put", "patch", "delete"}
    } | {
        "create_target",
        "start_scan",
        "stop_scan",
        "generate_report",
        "update_vulnerability_status",
    }

    for name in mutating_tool_names:
        properties = tools[name].parameters["properties"]
        assert "confirmation" in properties, name
        assert properties["confirmation"]["type"] == "boolean"


@pytest.mark.asyncio
async def test_representative_read_tool_calls_expected_path(monkeypatch):
    import acunetix_mcp.tools.openapi_coverage as coverage

    fake = FakeAcunetix()
    monkeypatch.setattr(coverage, "acunetix", fake)
    tools = {tool.name: tool for tool in await create_server().list_tools()}

    result = await tools["list_users"].fn(limit=25)

    assert result["success"] is True
    assert fake.calls == [("get", "/users", {"l": 25}, None)]


@pytest.mark.asyncio
async def test_representative_path_tool_calls_expected_path(monkeypatch):
    import acunetix_mcp.tools.openapi_coverage as coverage

    fake = FakeAcunetix()
    monkeypatch.setattr(coverage, "acunetix", fake)
    tools = {tool.name: tool for tool in await create_server().list_tools()}

    await tools["download_report"].fn(path_params={"descriptor": "abc123"})

    assert fake.calls == [("get", "/reports/download/abc123", {}, None)]


@pytest.mark.asyncio
async def test_representative_mutating_tool_is_blocked_by_default(monkeypatch):
    import acunetix_mcp.tools.openapi_coverage as coverage

    fake = FakeAcunetix()
    monkeypatch.setattr(coverage, "acunetix", fake)
    monkeypatch.setenv("ACUNETIX_READ_ONLY", "true")
    monkeypatch.setenv("ACUNETIX_MCP_CONFIG", "missing-test-config.yaml")
    tools = {tool.name: tool for tool in await create_server().list_tools()}

    result = await tools["create_user"].fn(body={"email": "a@example.com"}, confirmation=True)

    assert result["success"] is False
    assert result["error"]["type"] == "PolicyDenied"
    assert fake.calls == []


@pytest.mark.asyncio
async def test_representative_mutating_tool_calls_expected_method_when_allowed(monkeypatch):
    import acunetix_mcp.tools.openapi_coverage as coverage

    fake = FakeAcunetix()
    user_id = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setattr(coverage, "acunetix", fake)
    monkeypatch.setenv("ACUNETIX_READ_ONLY", "false")
    monkeypatch.setenv("ACUNETIX_REQUIRE_CONFIRMATION", "true")
    monkeypatch.setenv("ACUNETIX_MCP_CONFIG", "missing-test-config.yaml")
    tools = {tool.name: tool for tool in await create_server().list_tools()}

    result = await tools["update_user"].fn(
        path_params={"user_id": user_id},
        body={"first_name": "Ada"},
        confirmation=True,
    )

    assert result["success"] is True
    assert fake.calls == [("patch", f"/users/{user_id}", None, {"first_name": "Ada"})]
