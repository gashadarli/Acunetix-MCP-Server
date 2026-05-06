"""MCP resources that expose safe server metadata and operating guidance."""

from __future__ import annotations

import json
from typing import Any

import fastmcp

from .config import load_settings
from .tools.openapi_coverage import build_operation_catalog


def register_resources(mcp: fastmcp.FastMCP) -> None:
    @mcp.resource(
        "acunetix://tool-coverage",
        name="Acunetix Tool Coverage",
        description="Coverage summary for documented Acunetix API operations.",
        mime_type="application/json",
    )
    def tool_coverage() -> str:
        operations = build_operation_catalog()
        methods: dict[str, int] = {}
        for operation in operations:
            methods[operation.method.upper()] = methods.get(operation.method.upper(), 0) + 1
        return json.dumps(
            {
                "documented_operations": len(operations),
                "coverage": "full",
                "missing_operations": 0,
                "methods": methods,
            },
            indent=2,
            sort_keys=True,
        )

    @mcp.resource(
        "acunetix://policy",
        name="Acunetix Policy",
        description="Current safety policy settings with secrets redacted.",
        mime_type="application/json",
    )
    def policy_resource() -> str:
        settings = load_settings()
        return json.dumps(
            {
                "read_only": settings.read_only,
                "require_confirmation": settings.require_confirmation,
                "allowed_targets_count": len(settings.allowed_targets),
                "max_concurrent_scan_starts": settings.max_concurrent_scan_starts,
                "verify_ssl": settings.acunetix_verify_ssl,
                "api_base_url_configured": bool(settings.acunetix_base_url),
                "api_key_configured": bool(settings.acunetix_api_key),
            },
            indent=2,
            sort_keys=True,
        )

    @mcp.resource(
        "acunetix://openapi-summary",
        name="Acunetix OpenAPI Summary",
        description="Summary of domains and operation counts from the bundled Acunetix API documentation.",
        mime_type="application/json",
    )
    def openapi_summary() -> str:
        domains: dict[str, int] = {}
        for operation in build_operation_catalog():
            domain = operation.path.strip("/").split("/", 1)[0] or "root"
            domains[domain] = domains.get(domain, 0) + 1
        return json.dumps(
            {
                "source": "Acunetix-API-Documentation.yaml",
                "domains": dict(sorted(domains.items())),
            },
            indent=2,
            sort_keys=True,
        )

    @mcp.resource(
        "acunetix://configuration-template",
        name="Acunetix Configuration Template",
        description="Safe environment variable template for configuring the server.",
        mime_type="text/plain",
    )
    def configuration_template() -> str:
        return "\n".join(
            [
                "ACUNETIX_BASE_URL=https://10.0.244.136/",
                "ACUNETIX_API_KEY=replace-with-your-api-key",
                "ACUNETIX_VERIFY_SSL=false",
                "ACUNETIX_READ_ONLY=true",
                "ACUNETIX_REQUIRE_CONFIRMATION=true",
                "ACUNETIX_TARGET_ALLOWLIST=",
                "ACUNETIX_TIMEOUT_SECONDS=30",
                "ACUNETIX_MAX_CONCURRENT_SCAN_STARTS=1",
                "MCP_TRANSPORT=stdio",
                "MCP_SERVER_PORT=8080",
            ]
        )
