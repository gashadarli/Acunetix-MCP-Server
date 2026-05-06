"""Health MCP tool."""

from __future__ import annotations

from typing import Any

import fastmcp

from ..client import acunetix


def register_health_tools(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool(name="acunetix_health")
    async def acunetix_health() -> dict[str, Any]:
        """Check Acunetix MCP configuration and authenticated API reachability."""
        return await acunetix.health()
