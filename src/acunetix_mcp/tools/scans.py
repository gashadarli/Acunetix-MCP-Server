"""Scan management tools — start, list, status, abort, results, profiles."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix

# Well-known built-in scanning profile IDs in Acunetix.
# Users can also pass a custom profile_id from acunetix__list_scanning_profiles.
PROFILE_FULL_SCAN = "11111111-1111-1111-1111-111111111111"


def register_scan_tools(mcp: fastmcp.FastMCP) -> None:

    @mcp.tool(name="acunetix__list_scans")
    async def list_scans(
        target_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List scans in Acunetix, optionally filtered by target or status.

        Args:
            target_id: Only return scans for this target (UUID). If omitted,
                       returns recent scans across all targets.
            status:    Filter by scan status: 'processing', 'scheduled',
                       'running', 'pausing', 'paused', 'completed',
                       'aborted', 'failed', 'empty'.
            limit:     Max scans to return (default 20).
            offset:    Pagination cursor from a previous response.

        Returns:
            {
              "success": true,
              "data": {
                "scans": [
                  {
                    "scan_id": "uuid",
                    "target_id": "uuid",
                    "profile_name": "Full Scan",
                    "status": "completed",
                    "start_date": "2025-01-01T10:00:00Z",
                    "current_result_id": "uuid"   // use with acunetix__get_scan_status
                  }, ...
                ]
              }
            }
        """
        query_parts = []
        if target_id:
            query_parts.append(f"target_id:{target_id}")
        if status:
            query_parts.append(f"status:{status}")
        params: Dict[str, Any] = {"l": limit}
        if query_parts:
            params["q"] = ";".join(query_parts)
        if offset:
            params["c"] = offset
        return await acunetix.get("/scans", params=params)

    @mcp.tool(name="acunetix__start_scan")
    async def start_scan(
        target_id: str,
        profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start a new scan on a target immediately.

        Args:
            target_id:  UUID of the target to scan (from acunetix__list_targets
                        or acunetix__add_target).
            profile_id: Scan profile UUID. If omitted, the Full Scan profile is
                        used. To see available profiles and their IDs, call
                        acunetix__list_scanning_profiles first.

                        Common built-in profiles:
                        - Full Scan (default):         11111111-1111-1111-1111-111111111111
                        - High Risk Vulnerabilities:   11111111-1111-1111-1111-111111111112
                        - SQL Injection:               11111111-1111-1111-1111-111111111113
                        - XSS:                         11111111-1111-1111-1111-111111111115
                        - Crawl Only:                  11111111-1111-1111-1111-111111111116

        Returns:
            {
              "success": true,
              "data": {
                "scan_id": "uuid",    // use with acunetix__get_scan_status
                "target_id": "uuid",
                "profile_name": "Full Scan",
                "status": "processing"
              }
            }
        """
        body: Dict[str, Any] = {
            "target_id": target_id,
            "profile_id": profile_id or PROFILE_FULL_SCAN,
            "schedule": {
                "disable": False,
                "start_date": None,     # null = start immediately
                "time_sensitive": False,
            },
        }
        return await acunetix.post("/scans", body=body)

    @mcp.tool(name="acunetix__get_scan_status")
    async def get_scan_status(scan_id: str) -> Dict[str, Any]:
        """Get the current status and progress of a scan.

        Poll this tool while a scan is running to check when it completes.
        Once status is 'completed', use acunetix__get_scan_results or
        acunetix__list_vulnerabilities for findings.

        Args:
            scan_id: UUID of the scan (from acunetix__list_scans or
                     acunetix__start_scan).

        Returns:
            {
              "success": true,
              "data": {
                "scan_id": "uuid",
                "target_id": "uuid",
                "profile_name": "Full Scan",
                "status": "running" | "completed" | "aborted" | ...,
                "current_result": {
                  "result_id": "uuid",
                  "status": "running",
                  "start_date": "...",
                  "end_date": null,
                  "severity_counts": {
                    "critical": 0, "high": 3, "medium": 5,
                    "low": 12, "informational": 2
                  }
                }
              }
            }
        """
        return await acunetix.get(f"/scans/{scan_id}")

    @mcp.tool(name="acunetix__abort_scan")
    async def abort_scan(scan_id: str) -> Dict[str, Any]:
        """Abort (stop) a currently running scan.

        Args:
            scan_id: UUID of the scan to stop.

        Returns:
            {"success": true, "data": null, "message": "Operation completed successfully"}
        """
        return await acunetix.post(f"/scans/{scan_id}/abort")

    @mcp.tool(name="acunetix__get_scan_results")
    async def get_scan_results(
        scan_id: str,
        limit: Optional[int] = 10,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List result sessions for a scan (each run of the scan is one result).

        Use the result_id values from here with acunetix__get_scan_result or
        acunetix__get_scan_statistics for detailed per-session breakdowns.

        Args:
            scan_id: UUID of the scan.
            limit:   Max results to return (default 10).
            offset:  Pagination cursor.

        Returns:
            List of scan session result objects with result_id, status,
            start_date, end_date, and vuln severity counts.
        """
        params: Dict[str, Any] = {"l": limit}
        if offset:
            params["c"] = offset
        return await acunetix.get(f"/scans/{scan_id}/results", params=params)

    @mcp.tool(name="acunetix__list_scanning_profiles")
    async def list_scanning_profiles() -> Dict[str, Any]:
        """List all available scan profiles (built-in and custom).

        Use the profile_id values from this list when calling
        acunetix__start_scan to target specific vulnerability classes.

        Returns:
            {
              "success": true,
              "data": {
                "scanning_profiles": [
                  {
                    "profile_id": "11111111-...",
                    "name": "Full Scan",
                    "custom": false
                  }, ...
                ]
              }
            }
        """
        return await acunetix.get("/scanning_profiles")
