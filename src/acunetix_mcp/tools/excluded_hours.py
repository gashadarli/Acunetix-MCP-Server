"""Excluded Hours profile MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_excluded_hours_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_excluded_hours_profiles() -> Dict[str, Any]:
        """
        Get all Excluded Hours Profiles.
        Excluded hours define time windows during which scanning is paused.
        """
        return await acunetix.get("/excluded_hours_profiles")

    @mcp.tool()
    async def create_excluded_hours_profile(
        name: str,
        excluded_hours: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create a new Excluded Hours Profile.
        name: Profile name.
        excluded_hours: List of exclusion windows. Each item has:
          - 'day_of_week': 0-6 (0=Sunday)
          - 'start': Start hour (0-23)
          - 'end': End hour (0-23)
        """
        return await acunetix.post(
            "/excluded_hours_profiles",
            body={"name": name, "excluded_hours": excluded_hours},
        )

    @mcp.tool()
    async def get_excluded_hours_profile(excluded_hours_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Excluded Hours Profile.
        """
        return await acunetix.get(f"/excluded_hours_profiles/{excluded_hours_id}")

    @mcp.tool()
    async def update_excluded_hours_profile(
        excluded_hours_id: str,
        name: Optional[str] = None,
        excluded_hours: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Modify an Excluded Hours Profile.
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if excluded_hours is not None:
            body["excluded_hours"] = excluded_hours
        return await acunetix.patch(f"/excluded_hours_profiles/{excluded_hours_id}", body=body)

    @mcp.tool()
    async def delete_excluded_hours_profile(excluded_hours_id: str) -> Dict[str, Any]:
        """
        Delete an Excluded Hours Profile.
        """
        return await acunetix.delete(f"/excluded_hours_profiles/{excluded_hours_id}")
