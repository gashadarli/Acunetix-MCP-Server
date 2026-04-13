"""Target management tools — acunetix__list_targets, acunetix__get_target, acunetix__add_target."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix


def register_target_tools(mcp: fastmcp.FastMCP) -> None:

    @mcp.tool(name="acunetix__list_targets")
    async def list_targets(
        search: Optional[str] = None,
        limit: Optional[int] = 50,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all scan targets in Acunetix.

        Use this to get the target inventory — addresses, criticalities,
        last scan dates, and target IDs needed for starting scans.

        Args:
            search: Filter targets whose address or description contains this
                    string (case-insensitive substring). For example: 'sima',
                    'azincloud', 'example.com'.
            limit:  Max number of targets to return (default 50).
            offset: Pagination cursor from a previous response (pass the
                    'next_cursor' value to get the next page).

        Returns:
            {
              "success": true,
              "data": {
                "targets": [
                  {
                    "target_id": "uuid",
                    "address": "https://example.com",
                    "description": "...",
                    "criticality": 30,          // 0=none 10=low 20=med 30=high 40=critical
                    "last_scan_date": "2025-01-01T00:00:00Z" | null,
                    "continuous_scan": false
                  }, ...
                ],
                "pagination": { "next_cursor": "...", "count": 50 }
              }
            }
        """
        params: Dict[str, Any] = {"l": limit}
        if search:
            params["q"] = f"text:{search}"
        if offset:
            params["c"] = offset
        return await acunetix.get("/targets", params=params)

    @mcp.tool(name="acunetix__get_target")
    async def get_target(target_id: str) -> Dict[str, Any]:
        """Get detailed information about a single scan target.

        Args:
            target_id: The UUID of the target (from acunetix__list_targets).

        Returns:
            Full target object including address, description, criticality,
            tags, scan schedule, and sensor settings.
        """
        return await acunetix.get(f"/targets/{target_id}")

    @mcp.tool(name="acunetix__add_target")
    async def add_target(
        address: str,
        description: Optional[str] = None,
        criticality: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """Create a new scan target in Acunetix.

        Args:
            address:     Full URL of the target application, e.g.
                         'https://app.example.com'. Include scheme and port
                         if non-standard.
            description: Optional human-readable label for this target.
            criticality: Business criticality score:
                         0=none, 10=low (default), 20=medium,
                         30=high, 40=critical.

        Returns:
            The newly created target object, including its target_id which
            you need to start a scan.
        """
        body: Dict[str, Any] = {
            "address": address,
            "type": "default",
            "criticality": criticality,
        }
        if description:
            body["description"] = description
        return await acunetix.post("/targets", body=body)
