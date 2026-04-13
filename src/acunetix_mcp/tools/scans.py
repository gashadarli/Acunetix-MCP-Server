"""Scan management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_scan_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_scans(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of all Scans. Supports pagination via cursor/limit.
        query examples: 'threat:3' (high severity), 'target_id:UUID', 'status:completed'
        sort examples: 'start_date:desc'
        """
        return await acunetix.get(
            "/scans",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def schedule_scan(
        target_id: str,
        profile_id: str = "11111111-1111-1111-1111-111111111111",
        report_template_id: Optional[str] = None,
        schedule_disable: bool = False,
        schedule_start_date: Optional[str] = None,
        schedule_time_sensitive: bool = False,
        schedule_recurrence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a Scan for a Target.
        profile_id: '11111111-1111-1111-1111-111111111111' = Full Scan (default)
        Common profile_ids:
          - '11111111-1111-1111-1111-111111111111' = Full Scan
          - '11111111-1111-1111-1111-111111111112' = High Risk Vulnerabilities
          - '11111111-1111-1111-1111-111111111116' = Crawl Only
          - '11111111-1111-1111-1111-111111111115' = XSS
          - '11111111-1111-1111-1111-111111111113' = SQL Injection
        schedule_start_date: ISO 8601 format or null for immediate
        schedule_recurrence: iCal RRULE format for recurring scans
        """
        schedule: Dict[str, Any] = {
            "disable": schedule_disable,
            "start_date": schedule_start_date,
            "time_sensitive": schedule_time_sensitive,
        }
        if schedule_recurrence:
            schedule["recurrence"] = schedule_recurrence

        body: Dict[str, Any] = {
            "target_id": target_id,
            "profile_id": profile_id,
            "schedule": schedule,
        }
        if report_template_id:
            body["report_template_id"] = report_template_id

        return await acunetix.post("/scans", body=body)

    @mcp.tool()
    async def get_scan(scan_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Scan by its ID.
        Returns status, target, profile, schedule, and current result info.
        """
        return await acunetix.get(f"/scans/{scan_id}")

    @mcp.tool()
    async def update_scan(
        scan_id: str,
        profile_id: Optional[str] = None,
        report_template_id: Optional[str] = None,
        schedule_disable: Optional[bool] = None,
        schedule_start_date: Optional[str] = None,
        schedule_time_sensitive: Optional[bool] = None,
        schedule_recurrence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Modify an existing Scan (profile, schedule, report template).
        """
        body: Dict[str, Any] = {}
        schedule: Dict[str, Any] = {}

        if profile_id:
            body["profile_id"] = profile_id
        if report_template_id:
            body["report_template_id"] = report_template_id
        if schedule_disable is not None:
            schedule["disable"] = schedule_disable
        if schedule_start_date is not None:
            schedule["start_date"] = schedule_start_date
        if schedule_time_sensitive is not None:
            schedule["time_sensitive"] = schedule_time_sensitive
        if schedule_recurrence is not None:
            schedule["recurrence"] = schedule_recurrence
        if schedule:
            body["schedule"] = schedule

        return await acunetix.patch(f"/scans/{scan_id}", body=body)

    @mcp.tool()
    async def remove_scan(scan_id: str) -> Dict[str, Any]:
        """
        Delete a Scan and all its results.
        WARNING: This is irreversible!
        """
        return await acunetix.delete(f"/scans/{scan_id}")

    @mcp.tool()
    async def abort_scan(scan_id: str) -> Dict[str, Any]:
        """
        Abort a currently running Scan.
        """
        return await acunetix.post(f"/scans/{scan_id}/abort")

    @mcp.tool()
    async def resume_scan(scan_id: str) -> Dict[str, Any]:
        """
        Resume a previously aborted Scan.
        """
        return await acunetix.post(f"/scans/{scan_id}/resume")

    @mcp.tool()
    async def trigger_scan(scan_id: str) -> Dict[str, Any]:
        """
        Trigger a new Scan session for an existing scheduled Scan.
        """
        return await acunetix.post(f"/scans/{scan_id}/trigger")

    @mcp.tool()
    async def get_scan_result_history(
        scan_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Scan Results across all Scan sessions/runs for a given Scan.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results",
            params={"c": cursor, "l": limit, "s": sort},
        )

    @mcp.tool()
    async def get_continuous_scans(
        target_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List Continuous Scans for a Target.
        """
        return await acunetix.get(
            f"/targets/{target_id}/continuous_scan/list",
            params={"c": cursor, "l": limit, "s": sort},
        )
