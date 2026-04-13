"""Scanning profile (scan type) management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_scanning_profile_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_scanning_profiles() -> Dict[str, Any]:
        """
        Get all available Scanning Profiles (Scan Types).
        Built-in profiles include:
        - Full Scan (11111111-1111-1111-1111-111111111111)
        - High Risk Vulnerabilities (11111111-1111-1111-1111-111111111112)
        - XSS (11111111-1111-1111-1111-111111111115)
        - SQL Injection (11111111-1111-1111-1111-111111111113)
        - Weak Passwords (11111111-1111-1111-1111-111111111117)
        - Crawl Only (11111111-1111-1111-1111-111111111116)
        - Malware Detection (11111111-1111-1111-1111-111111111120)
        """
        return await acunetix.get("/scanning_profiles")

    @mcp.tool()
    async def get_scanning_profile(scanning_profile_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Scanning Profile.
        """
        return await acunetix.get(f"/scanning_profiles/{scanning_profile_id}")

    @mcp.tool()
    async def create_scanning_profile(
        name: str,
        checks: Optional[List[str]] = None,
        sort_order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a custom Scanning Profile.
        name: Profile name.
        checks: List of check names to EXCLUDE. Empty list means all checks run.
        sort_order: Display order (higher = lower in list).
        """
        body: Dict[str, Any] = {"name": name, "checks": checks or []}
        if sort_order is not None:
            body["sort_order"] = sort_order
        return await acunetix.post("/scanning_profiles", body=body)

    @mcp.tool()
    async def update_scanning_profile(
        scanning_profile_id: str,
        name: Optional[str] = None,
        checks: Optional[List[str]] = None,
        sort_order: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Modify a custom Scanning Profile.
        Note: Built-in profiles cannot be modified.
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if checks is not None:
            body["checks"] = checks
        if sort_order is not None:
            body["sort_order"] = sort_order
        return await acunetix.patch(f"/scanning_profiles/{scanning_profile_id}", body=body)

    @mcp.tool()
    async def delete_scanning_profile(scanning_profile_id: str) -> Dict[str, Any]:
        """
        Delete a custom Scanning Profile.
        Note: Built-in profiles cannot be deleted.
        """
        return await acunetix.delete(f"/scanning_profiles/{scanning_profile_id}")
