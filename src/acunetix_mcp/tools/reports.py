"""Report MCP tools."""

from __future__ import annotations

from typing import Any, Literal

import fastmcp

from ..audit import audit_event
from ..client import acunetix
from ..policy import PolicyEngine, policy_error
from .common import validate_limit, validate_uuid


ReportSourceType = Literal["scan", "target", "scan_result"]


def register_report_tools(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool(name="list_report_templates")
    async def list_report_templates() -> dict[str, Any]:
        """List report templates that can be used with generate_report."""
        return await acunetix.get("/report_templates")

    @mcp.tool(name="list_reports")
    async def list_reports(
        limit: int | None = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        """List generated Acunetix reports."""
        params: dict[str, Any] = {"l": validate_limit(limit)}
        if offset:
            params["c"] = offset
        return await acunetix.get("/reports", params=params)

    @mcp.tool(name="get_report")
    async def get_report(report_id: str) -> dict[str, Any]:
        """Get one generated Acunetix report by report UUID."""
        error = validate_uuid(report_id, "report_id")
        if error:
            return error
        return await acunetix.get(f"/reports/{report_id}")

    @mcp.tool(name="generate_report")
    async def generate_report(
        template_id: str,
        source_type: ReportSourceType,
        source_id_list: list[str],
        confirmation: bool = False,
    ) -> dict[str, Any]:
        """Generate an Acunetix report after policy and confirmation checks."""
        template_error = validate_uuid(template_id, "template_id")
        if template_error:
            return template_error
        if source_type not in {"scan", "target", "scan_result"}:
            return {
                "success": False,
                "error": {
                    "message": "source_type must be scan, target, or scan_result.",
                    "type": "ValidationError",
                },
            }
        if not source_id_list:
            return {
                "success": False,
                "error": {
                    "message": "source_id_list must contain at least one UUID.",
                    "type": "ValidationError",
                },
            }
        for index, source_id in enumerate(source_id_list):
            source_error = validate_uuid(source_id, f"source_id_list[{index}]")
            if source_error:
                return source_error

        policy = PolicyEngine()
        decision = policy.check_action(
            "generate_report",
            confirmed=confirmation,
        )
        audit_event(
            "generate_report",
            allowed=decision.allowed,
            reason=decision.reason,
            details={
                "template_id": template_id,
                "source_type": source_type,
                "source_count": len(source_id_list),
            },
        )
        if not decision.allowed:
            return policy_error(decision)

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
