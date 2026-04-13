"""Vulnerability tools — list, get details, update status, list types."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix


def register_vulnerability_tools(mcp: fastmcp.FastMCP) -> None:

    @mcp.tool(name="acunetix__list_vulnerabilities")
    async def list_vulnerabilities(
        target_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = 50,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List vulnerabilities found across all scans (or filtered to one target).

        Args:
            target_id: Only return vulnerabilities for this target UUID.
            severity:  Filter by severity level:
                       'critical', 'high', 'medium', 'low', 'informational'
                       (maps to 4, 3, 2, 1, 0 internally).
            status:    Filter by triage status: 'open', 'fixed', 'ignored',
                       'false_positive'.
            search:    Substring search in vulnerability name/description.
            limit:     Max vulnerabilities to return (default 50).
            offset:    Pagination cursor.

        Returns:
            List of vulnerability objects with vuln_id, severity, name,
            target_id, affects_url, status, and discovery date.
        """
        severity_map = {
            "critical": 4, "high": 3, "medium": 2,
            "low": 1, "informational": 0,
        }
        query_parts = []
        if target_id:
            query_parts.append(f"target_id:{target_id}")
        if severity and severity.lower() in severity_map:
            query_parts.append(f"severity:{severity_map[severity.lower()]}")
        if status:
            query_parts.append(f"status:{status}")
        if search:
            query_parts.append(f"text:{search}")

        params: Dict[str, Any] = {"l": limit}
        if query_parts:
            params["q"] = ";".join(query_parts)
        if offset:
            params["c"] = offset
        return await acunetix.get("/vulnerabilities", params=params)

    @mcp.tool(name="acunetix__get_vulnerability")
    async def get_vulnerability(vuln_id: str) -> Dict[str, Any]:
        """Get full details of a specific vulnerability.

        Returns the description, impact, remediation guidance, CVSS score,
        affected URL, HTTP request/response evidence, and OWASP/CVE references.

        Args:
            vuln_id: Vulnerability UUID (from acunetix__list_vulnerabilities).
        """
        return await acunetix.get(f"/vulnerabilities/{vuln_id}")

    @mcp.tool(name="acunetix__update_vulnerability_status")
    async def update_vulnerability_status(
        vuln_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """Update the triage status of a vulnerability.

        Args:
            vuln_id: Vulnerability UUID.
            status:  New status — one of:
                     'open'          — active, needs attention
                     'false_positive'— mark as not a real issue
                     'ignored'       — acknowledged, won't fix
                     'fixed'         — resolved and confirmed

        Returns:
            {"success": true, "data": null, "message": "Operation completed successfully"}
        """
        valid = {"open", "false_positive", "ignored", "fixed"}
        if status not in valid:
            return {
                "success": False,
                "error": {
                    "message": f"Invalid status '{status}'. Must be one of: {sorted(valid)}"
                },
            }
        return await acunetix.put(
            f"/vulnerabilities/{vuln_id}/status",
            body={"status": status},
        )

    @mcp.tool(name="acunetix__list_vulnerability_types")
    async def list_vulnerability_types(
        limit: Optional[int] = 50,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List vulnerability types/categories with occurrence counts.

        Useful for understanding the distribution of issues across all
        targets (e.g., how many SQL Injection, XSS, etc. findings exist).

        Args:
            limit:  Max types to return (default 50).
            offset: Pagination cursor.
        """
        params: Dict[str, Any] = {"l": limit}
        if offset:
            params["c"] = offset
        return await acunetix.get("/vulnerability_types", params=params)
