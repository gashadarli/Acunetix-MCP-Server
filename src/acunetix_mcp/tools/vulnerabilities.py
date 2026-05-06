"""Vulnerability MCP tools."""

from __future__ import annotations

from typing import Any

import fastmcp

from ..audit import audit_event
from ..client import acunetix
from ..policy import PolicyEngine, policy_error
from .common import validate_limit, validate_uuid


SEVERITY_MAP = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "informational": 0,
}
VALID_VULN_STATUSES = {"open", "fixed", "ignored", "false_positive"}


def register_vulnerability_tools(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool(name="list_vulnerabilities")
    async def list_vulnerabilities(
        target_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int | None = 50,
        offset: str | None = None,
    ) -> dict[str, Any]:
        """List Acunetix vulnerabilities with optional target/severity/status filters."""
        query_parts: list[str] = []
        if target_id:
            error = validate_uuid(target_id, "target_id")
            if error:
                return error
            query_parts.append(f"target_id:{target_id}")
        if severity:
            normalized = severity.lower()
            if normalized not in SEVERITY_MAP:
                return {
                    "success": False,
                    "error": {
                        "message": f"severity must be one of {sorted(SEVERITY_MAP)}.",
                        "type": "ValidationError",
                    },
                }
            query_parts.append(f"severity:{SEVERITY_MAP[normalized]}")
        if status:
            if status not in VALID_VULN_STATUSES:
                return {
                    "success": False,
                    "error": {
                        "message": f"status must be one of {sorted(VALID_VULN_STATUSES)}.",
                        "type": "ValidationError",
                    },
                }
            query_parts.append(f"status:{status}")
        if search:
            query_parts.append(f"text:{search}")

        params: dict[str, Any] = {"l": validate_limit(limit)}
        if query_parts:
            params["q"] = ";".join(query_parts)
        if offset:
            params["c"] = offset
        return await acunetix.get("/vulnerabilities", params=params)

    @mcp.tool(name="get_vulnerability")
    async def get_vulnerability(vuln_id: str) -> dict[str, Any]:
        """Get details for one Acunetix vulnerability by vulnerability UUID."""
        error = validate_uuid(vuln_id, "vuln_id")
        if error:
            return error
        return await acunetix.get(f"/vulnerabilities/{vuln_id}")

    @mcp.tool(name="update_vulnerability_status")
    async def update_vulnerability_status(
        vuln_id: str,
        status: str,
        confirmation: bool = False,
    ) -> dict[str, Any]:
        """Update a vulnerability status after policy and confirmation checks."""
        error = validate_uuid(vuln_id, "vuln_id")
        if error:
            return error
        if status not in VALID_VULN_STATUSES:
            return {
                "success": False,
                "error": {
                    "message": f"status must be one of {sorted(VALID_VULN_STATUSES)}.",
                    "type": "ValidationError",
                },
            }

        policy = PolicyEngine()
        decision = policy.check_action(
            "update_vulnerability_status",
            confirmed=confirmation,
        )
        audit_event(
            "update_vulnerability_status",
            allowed=decision.allowed,
            reason=decision.reason,
            details={"vuln_id": vuln_id, "status": status},
        )
        if not decision.allowed:
            return policy_error(decision)
        return await acunetix.put(
            f"/vulnerabilities/{vuln_id}/status",
            body={"status": status},
        )
