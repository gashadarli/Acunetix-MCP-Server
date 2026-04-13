"""Report management tools — templates, generate, list, get."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_report_tools(mcp: fastmcp.FastMCP) -> None:

    @mcp.tool(name="acunetix__list_report_templates")
    async def list_report_templates() -> Dict[str, Any]:
        """List all available report templates.

        Call this first to find the template_id you need before calling
        acunetix__generate_report.

        Common templates include: Executive Summary, Developer Report,
        Quick Report, Affected Items, Compliance reports (PCI DSS, HIPAA,
        ISO 27001, OWASP Top 10, etc.).

        Returns:
            List of templates with template_id, name, and report type.
        """
        return await acunetix.get("/report_templates")

    @mcp.tool(name="acunetix__generate_report")
    async def generate_report(
        template_id: str,
        source_type: str,
        source_id_list: List[str],
    ) -> Dict[str, Any]:
        """Generate a new report for one or more scans or targets.

        Args:
            template_id:    Template UUID from acunetix__list_report_templates.
            source_type:    What the report covers:
                            'scan'        — one or more scan UUIDs
                            'target'      — one or more target UUIDs
                            'scan_result' — one or more scan result session UUIDs
            source_id_list: List of UUIDs matching the source_type.

        Returns:
            Report object with report_id. Use acunetix__get_report to check
            status and retrieve the download descriptor once generation is done.

        Example:
            Generate a PDF for the last scan of target X:
              template_id    = "..."   (from list_report_templates)
              source_type    = "scan"
              source_id_list = ["<scan_uuid>"]
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

    @mcp.tool(name="acunetix__list_reports")
    async def list_reports(
        limit: Optional[int] = 20,
        offset: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all generated reports.

        Args:
            limit:  Max reports to return (default 20).
            offset: Pagination cursor.

        Returns:
            List of report objects with report_id, template name, status
            ('processing' | 'completed' | 'failed'), and creation date.
        """
        params: Dict[str, Any] = {"l": limit}
        if offset:
            params["c"] = offset
        return await acunetix.get("/reports", params=params)

    @mcp.tool(name="acunetix__get_report")
    async def get_report(report_id: str) -> Dict[str, Any]:
        """Get details and download information for a specific report.

        Once status is 'completed', the response includes a 'download'
        descriptor list. Share those descriptors with the user or use them
        to retrieve the actual PDF/HTML file.

        Args:
            report_id: UUID of the report (from acunetix__list_reports or
                       acunetix__generate_report).

        Returns:
            Report object including status and download descriptors.
        """
        return await acunetix.get(f"/reports/{report_id}")
