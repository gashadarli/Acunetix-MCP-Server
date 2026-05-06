"""MCP prompts that guide safe Acunetix workflows."""

from __future__ import annotations

from typing import Any

import fastmcp


def register_prompts(mcp: fastmcp.FastMCP) -> None:
    @mcp.prompt(
        name="acunetix_inventory_summary",
        description="Plan a read-only inventory summary using Acunetix targets, groups, scans, and reports.",
    )
    def acunetix_inventory_summary() -> str:
        return (
            "Create a read-only Acunetix inventory summary. Use acunetix_health, "
            "list_target_groups, list_targets, list_scans, and list_reports. "
            "Do not start scans or change Acunetix state. Summarize counts, "
            "notable statuses, stale scans, and any API errors clearly."
        )

    @mcp.prompt(
        name="acunetix_scan_status_report",
        description="Guide an assistant through checking scan status for a specific scan ID.",
    )
    def acunetix_scan_status_report(scan_id: str) -> str:
        return (
            f"Check the Acunetix scan status for scan_id {scan_id}. Use "
            "get_scan_status first. If the scan has current result metadata, "
            "summarize status, progress, start/end times, and severity counts. "
            "Keep the workflow read-only."
        )

    @mcp.prompt(
        name="acunetix_vulnerability_triage",
        description="Guide safe vulnerability triage without modifying finding status by default.",
    )
    def acunetix_vulnerability_triage(
        target_id: str | None = None,
        severity: str | None = None,
    ) -> str:
        filters: list[str] = []
        if target_id:
            filters.append(f"target_id={target_id}")
        if severity:
            filters.append(f"severity={severity}")
        filter_text = ", ".join(filters) if filters else "no extra filters"
        return (
            "Perform read-only Acunetix vulnerability triage with "
            f"{filter_text}. Use list_vulnerabilities and get_vulnerability. "
            "Group findings by severity and affected URL, call out remediation "
            "themes, and do not call update_vulnerability_status unless the user "
            "explicitly requests it and confirmation is provided."
        )

    @mcp.prompt(
        name="acunetix_safe_scan_start_checklist",
        description="Checklist to evaluate whether a requested scan start is allowed and safe.",
    )
    def acunetix_safe_scan_start_checklist(target_id: str) -> str:
        return (
            f"Before starting a scan for target_id {target_id}, verify policy: "
            "check whether read-only mode is enabled, confirm the target is in "
            "the allowlist when configured, identify the intended scan profile, "
            "and ask for explicit confirmation. Only call start_scan with "
            "confirmation=true after the user clearly approves."
        )
