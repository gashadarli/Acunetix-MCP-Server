"""WAF (Web Application Firewall) uploader MCP tools."""

from typing import Any, Dict
import fastmcp

from ..client import acunetix


def register_waf_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_wafs() -> Dict[str, Any]:
        """
        Get all configured WAF (Web Application Firewall) integrations.
        Supported WAFs: AWS WAF, F5, Fortinet FortiWeb, Imperva, Modsec, etc.
        """
        return await acunetix.get("/wafs")

    @mcp.tool()
    async def create_waf(
        name: str,
        waf_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new WAF integration for vulnerability export.
        waf_type: 'awswaf', 'f5', 'fortiweb', 'imperva', 'modsec'
        config: WAF-specific configuration (credentials, endpoints).
        """
        return await acunetix.post(
            "/wafs",
            body={"name": name, "platform": waf_type, **config},
        )

    @mcp.tool()
    async def get_waf(waf_id: str) -> Dict[str, Any]:
        """
        Get details of a specific WAF integration.
        """
        return await acunetix.get(f"/wafs/{waf_id}")

    @mcp.tool()
    async def update_waf(
        waf_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Modify an existing WAF integration configuration.
        """
        return await acunetix.patch(f"/wafs/{waf_id}", body=config)

    @mcp.tool()
    async def delete_waf(waf_id: str) -> Dict[str, Any]:
        """
        Delete a WAF integration.
        """
        return await acunetix.delete(f"/wafs/{waf_id}")

    @mcp.tool()
    async def check_waf_connection(waf_id: str) -> Dict[str, Any]:
        """
        Test the connection to a saved WAF integration.
        """
        return await acunetix.get(f"/wafs/{waf_id}/check_connection")

    @mcp.tool()
    async def check_waf_connection_test(
        waf_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Test WAF connection without saving the configuration first.
        """
        return await acunetix.post("/wafs/check_connection", body=waf_config)
