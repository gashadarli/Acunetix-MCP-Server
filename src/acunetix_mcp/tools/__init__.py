"""MCP tool registration."""

from .health import register_health_tools
from .openapi_coverage import coverage_report, register_openapi_tools
from .reports import register_report_tools
from .scans import register_scan_tools
from .targets import register_target_tools
from .vulnerabilities import register_vulnerability_tools


HAND_WRITTEN_TOOL_NAMES = {
    "acunetix_health",
    "list_targets",
    "get_target",
    "list_target_groups",
    "get_target_group",
    "create_target",
    "list_scans",
    "get_scan_status",
    "list_scanning_profiles",
    "start_scan",
    "stop_scan",
    "list_vulnerabilities",
    "get_vulnerability",
    "update_vulnerability_status",
    "list_report_templates",
    "list_reports",
    "get_report",
    "generate_report",
}


def register_all_tools(mcp) -> None:
    register_health_tools(mcp)
    register_target_tools(mcp)
    register_scan_tools(mcp)
    register_vulnerability_tools(mcp)
    register_report_tools(mcp)
    # Existing hand-written tools keep ergonomic signatures for common
    # workflows. The OpenAPI registrar fills every remaining documented
    # operation with a fixed per-operation tool.
    register_openapi_tools(mcp, skip_names=HAND_WRITTEN_TOOL_NAMES)


__all__ = ["coverage_report", "register_all_tools", "register_openapi_tools"]
