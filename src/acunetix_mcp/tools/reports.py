"""Report and export management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_report_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_report_templates() -> Dict[str, Any]:
        """
        Get all available Report Templates.
        Use template_id from this list when generating reports.
        Common templates: Executive Summary, Developer Report, Quick Report,
        Compliance (PCI DSS, HIPAA, ISO 27001, etc.)
        """
        return await acunetix.get("/report_templates")

    @mcp.tool()
    async def get_reports(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of all generated Reports.
        """
        return await acunetix.get(
            "/reports",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def generate_new_report(
        template_id: str,
        source_type: str,
        source_id_list: List[str],
    ) -> Dict[str, Any]:
        """
        Generate a new Report.
        template_id: ID from get_report_templates (e.g., report template UUID)
        source_type: 'scan', 'target', 'scan_result'
        source_id_list: List of scan/target/result IDs to include in the report
        """
        return await acunetix.post(
            "/reports",
            body={
                "template_id": template_id,
                "source": {
                    "list_type": source_type,
                    "id_list": source_id_list,
                },
            },
        )

    @mcp.tool()
    async def get_report(report_id: str) -> Dict[str, Any]:
        """
        Get details and download links for a specific Report.
        """
        return await acunetix.get(f"/reports/{report_id}")

    @mcp.tool()
    async def remove_report(report_id: str) -> Dict[str, Any]:
        """
        Delete a specific Report.
        """
        return await acunetix.delete(f"/reports/{report_id}")

    @mcp.tool()
    async def remove_reports(report_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple Reports at once.
        """
        return await acunetix.post(
            "/reports/delete",
            body={"id_list": report_ids},
        )

    @mcp.tool()
    async def repeat_report(report_id: str) -> Dict[str, Any]:
        """
        Re-generate an existing Report (useful after new scans).
        """
        return await acunetix.post(f"/reports/{report_id}/repeat")

    @mcp.tool()
    async def get_export_types() -> Dict[str, Any]:
        """
        Get all available Export Types (e.g., XML, JSON, CSV, PDF formats for
        specific security tools like OWASP ZAP, Metasploit, etc.).
        """
        return await acunetix.get("/export_types")

    @mcp.tool()
    async def create_export(
        export_id_type: str,
        source_type: str,
        source_id_list: List[str],
    ) -> Dict[str, Any]:
        """
        Export scan data in a specific format.
        export_id_type: Export type ID from get_export_types
        source_type: 'scan', 'target', 'scan_result', 'vulnerability'
        source_id_list: List of IDs to export
        """
        return await acunetix.post(
            "/exports",
            body={
                "export_id": export_id_type,
                "source": {
                    "list_type": source_type,
                    "id_list": source_id_list,
                },
            },
        )

    @mcp.tool()
    async def get_export(export_id: str) -> Dict[str, Any]:
        """
        Get details and download link for a specific Export.
        """
        return await acunetix.get(f"/exports/{export_id}")

    @mcp.tool()
    async def remove_export(export_id: str) -> Dict[str, Any]:
        """
        Delete a specific Export.
        """
        return await acunetix.delete(f"/exports/{export_id}")

    @mcp.tool()
    async def remove_exports(export_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple Exports at once.
        """
        return await acunetix.post(
            "/exports/delete",
            body={"id_list": export_ids},
        )

    @mcp.tool()
    async def download_report(descriptor: str) -> Dict[str, Any]:
        """
        Download a generated Report file (PDF/HTML).
        descriptor: The download descriptor from get_report response
        (found in the 'download' field of the report details).
        Returns the file as base64-encoded data.
        """
        return await acunetix.download(f"/reports/download/{descriptor}")
