"""Scan results MCP tools - vulnerabilities, crawl data, statistics, technologies."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_result_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_scan_result(result_id: str) -> Dict[str, Any]:
        """
        Get properties of a specific Scan Result (scan session).
        Returns status, start/end time, vulnerability counts by severity.
        """
        return await acunetix.get(f"/results/{result_id}")

    @mcp.tool()
    async def get_scan_vulnerabilities(
        scan_id: str,
        result_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all Vulnerabilities found during a specific Scan session.
        scan_id: The Scan ID.
        result_id: The Scan Result (session) ID.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def get_scan_vulnerability_detail(
        scan_id: str,
        result_id: str,
        vuln_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific Vulnerability in a Scan session.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}"
        )

    @mcp.tool()
    async def get_scan_vulnerability_detail_from_vuln_id(vuln_id: str) -> Dict[str, Any]:
        """
        Get Vulnerability details using only the vulnerability ID (no scan_id/result_id needed).
        This is a simpler alternative to get_scan_vulnerability_detail.
        """
        return await acunetix.get(f"/scan_vulnerabilities/{vuln_id}")

    @mcp.tool()
    async def get_scan_session_vulnerability_http_response(
        scan_id: str,
        result_id: str,
        vuln_id: str,
    ) -> Dict[str, Any]:
        """
        Get the raw HTTP response for a Vulnerability in a Scan session.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/http_response"
        )

    @mcp.tool()
    async def set_scan_session_vulnerability_status(
        scan_id: str,
        result_id: str,
        vuln_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """
        Update the status of a Vulnerability within a Scan session.
        status options: 'open', 'ignored', 'false_positive', 'fixed'
        """
        return await acunetix.put(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/status",
            body={"status": status},
        )

    @mcp.tool()
    async def recheck_scan_session_vulnerability(
        scan_id: str,
        result_id: str,
        vuln_id: str,
        profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Re-check a specific Vulnerability within a Scan session.
        """
        body: Dict[str, Any] = {}
        if profile_id:
            body["profile_id"] = profile_id
        return await acunetix.put(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/recheck",
            body=body,
        )

    @mcp.tool()
    async def recheck_scan_session_vulnerabilities(
        scan_id: str,
        result_id: str,
        vuln_ids: List[str],
        profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Re-check multiple Vulnerabilities within a Scan session.
        """
        body: Dict[str, Any] = {"vuln_id_list": vuln_ids}
        if profile_id:
            body["profile_id"] = profile_id
        return await acunetix.post(
            f"/scans/{scan_id}/results/{result_id}/vulnerabilities/recheck",
            body=body,
        )

    @mcp.tool()
    async def get_scan_vulnerability_types(
        scan_id: str,
        result_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerability Types found during a specific Scan session.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/vulnerability_types",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def get_scan_technologies(
        scan_id: str,
        result_id: str,
        query: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Technologies detected during a specific Scan session
        (frameworks, CMS, servers, etc.).
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/technologies",
            params={"q": query, "c": cursor, "l": limit, "s": sort},
        )

    @mcp.tool()
    async def get_scan_technology_vulnerabilities(
        scan_id: str,
        result_id: str,
        tech_id: str,
        loc_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerabilities for a specific Technology found during a Scan session.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/technologies/{tech_id}/locations/{loc_id}/vulnerabilities",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def get_target_technologies(target_id: str) -> Dict[str, Any]:
        """
        Get the latest Technologies found on a Target across all scans.
        """
        return await acunetix.get(f"/targets/{target_id}/technologies")

    @mcp.tool()
    async def get_target_technology_vulnerabilities(
        target_id: str,
        tech_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerabilities for a specific Technology on a Target.
        """
        return await acunetix.get(
            f"/targets/{target_id}/technologies/{tech_id}/vulnerabilities",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def search_crawl_data(
        scan_id: str,
        result_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search Crawl Data discovered during a Scan session.
        Without a query, returns the crawl root location.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/crawldata",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def get_location_details(
        scan_id: str,
        result_id: str,
        loc_id: str,
    ) -> Dict[str, Any]:
        """
        Get details of a specific Crawl Location (URL) found during a Scan.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/crawldata/{loc_id}"
        )

    @mcp.tool()
    async def get_location_children(
        scan_id: str,
        result_id: str,
        loc_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get child URLs of a specific Crawl Location.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/crawldata/{loc_id}/children",
            params={"c": cursor, "l": limit, "s": sort},
        )

    @mcp.tool()
    async def get_location_vulnerabilities(
        scan_id: str,
        result_id: str,
        loc_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get Vulnerabilities found at a specific Crawl Location.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/crawldata/{loc_id}/vulnerabilities",
            params={"c": cursor, "l": limit, "s": sort},
        )

    @mcp.tool()
    async def get_scan_statistics(
        scan_id: str,
        result_id: str,
    ) -> Dict[str, Any]:
        """
        Get Statistics for a Scan session including vulnerability counts by severity,
        total URLs scanned, scan duration, etc.
        """
        return await acunetix.get(
            f"/scans/{scan_id}/results/{result_id}/statistics"
        )
