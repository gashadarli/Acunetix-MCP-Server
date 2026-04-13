"""Tools package — registers all acunetix__ MCP tools."""

from .targets import register_target_tools
from .scans import register_scan_tools
from .vulnerabilities import register_vulnerability_tools
from .reports import register_report_tools
from .results import register_result_tools


def register_all_tools(mcp) -> None:
    """Register every tool module with the MCP server instance."""
    register_target_tools(mcp)
    register_scan_tools(mcp)
    register_vulnerability_tools(mcp)
    register_report_tools(mcp)
    register_result_tools(mcp)


__all__ = ["register_all_tools"]
