"""Scan result (session) tools — get result, get statistics."""

from typing import Any, Dict
import fastmcp

from ..client import acunetix


def register_result_tools(mcp: fastmcp.FastMCP) -> None:

    @mcp.tool(name="acunetix__get_scan_result")
    async def get_scan_result(result_id: str) -> Dict[str, Any]:
        """Get details of a specific scan result session.

        Each time a scan runs it produces a new result session. This tool
        returns metadata for one session: status, start/end time, and
        vulnerability severity counts.

        Args:
            result_id: UUID of the scan result session (obtained from
                       acunetix__get_scan_status → current_result.result_id,
                       or from acunetix__get_scan_results).

        Returns:
            {
              "success": true,
              "data": {
                "result_id": "uuid",
                "scan_id": "uuid",
                "status": "completed",
                "start_date": "2025-01-01T10:00:00Z",
                "end_date":   "2025-01-01T11:30:00Z",
                "severity_counts": {
                  "critical": 0,
                  "high": 4,
                  "medium": 7,
                  "low": 20,
                  "informational": 5
                }
              }
            }
        """
        return await acunetix.get(f"/results/{result_id}")

    @mcp.tool(name="acunetix__get_scan_statistics")
    async def get_scan_statistics(
        scan_id: str,
        result_id: str,
    ) -> Dict[str, Any]:
        """Get detailed statistics for a completed scan session.

        Returns vuln counts by severity, total URLs scanned, scan duration,
        and a breakdown of finding categories.

        Args:
            scan_id:   UUID of the scan.
            result_id: UUID of the scan result session.

        Returns:
            Statistics object with vulnerability severity breakdown,
            crawl statistics, and timing information.
        """
        return await acunetix.get(f"/scans/{scan_id}/results/{result_id}/statistics")
