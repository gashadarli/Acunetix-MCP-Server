"""Vulnerability management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_vulnerability_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_vulnerabilities(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of ALL Vulnerabilities found across all targets and scans.
        query examples: 'severity:3' (high), 'target_id:UUID', 'status:open'
        severity: 0=informational, 1=low, 2=medium, 3=high, 4=critical
        """
        return await acunetix.get(
            "/vulnerabilities",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def get_vulnerability_details(vuln_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Vulnerability, including
        description, impact, recommendation, request/response details, and CVSS scores.
        """
        return await acunetix.get(f"/vulnerabilities/{vuln_id}")

    @mcp.tool()
    async def get_vulnerability_http_response(vuln_id: str) -> Dict[str, Any]:
        """
        Get the raw HTTP response associated with a Vulnerability detection.
        """
        return await acunetix.get(f"/vulnerabilities/{vuln_id}/http_response")

    @mcp.tool()
    async def set_vulnerability_status(
        vuln_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """
        Update the status of a Vulnerability.
        status options: 'open', 'ignored', 'false_positive', 'fixed'
        """
        return await acunetix.put(
            f"/vulnerabilities/{vuln_id}/status",
            body={"status": status},
        )

    @mcp.tool()
    async def recheck_vulnerability(
        vuln_id: str,
        profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Re-check / verify a specific Vulnerability (schedules a targeted scan).
        profile_id: Optional scanning profile to use for recheck.
        """
        body: Dict[str, Any] = {}
        if profile_id:
            body["profile_id"] = profile_id
        return await acunetix.put(f"/vulnerabilities/{vuln_id}/recheck", body=body)

    @mcp.tool()
    async def recheck_vulnerabilities(
        vuln_ids: List[str],
        profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Re-check multiple Vulnerabilities at once.
        """
        body: Dict[str, Any] = {"vuln_id_list": vuln_ids}
        if profile_id:
            body["profile_id"] = profile_id
        return await acunetix.put("/vulnerabilities/recheck", body=body)

    @mcp.tool()
    async def create_vulnerability_issues(
        vuln_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Schedule creation of issues in the configured Issue Tracker for the given vulnerabilities.
        The issue tracker used is based on the integration linked to each vulnerability's target.
        """
        return await acunetix.post(
            "/vulnerabilities/issues",
            body={"vuln_id_list": vuln_ids},
        )

    @mcp.tool()
    async def get_vulnerability_types(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        view: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerability Types with counts. Shows which types of vulnerabilities
        were found and how many times.
        view: 'grouped' or 'flat'
        """
        return await acunetix.get(
            "/vulnerability_types",
            params={"c": cursor, "l": limit, "q": query, "s": sort, "v": view},
        )

    @mcp.tool()
    async def get_vulnerability_type(vt_id: str) -> Dict[str, Any]:
        """
        Get details about a specific Vulnerability Type.
        """
        return await acunetix.get(f"/vulnerability_types/{vt_id}")

    @mcp.tool()
    async def get_vulnerability_groups(
        group_type: Optional[str] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerability Groups (grouped by type or severity).
        group_type: 'severity', 'type', etc.
        """
        return await acunetix.get(
            "/vulnerability_groups",
            params={"group_type": group_type, "q": query, "s": sort},
        )
