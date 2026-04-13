"""Tools package - registers all Acunetix MCP tools."""

from .targets import register_target_tools
from .scans import register_scan_tools
from .vulnerabilities import register_vulnerability_tools
from .results import register_result_tools
from .reports import register_report_tools
from .users import register_user_tools
from .groups import register_group_tools
from .scanning_profiles import register_scanning_profile_tools
from .workers import register_worker_tools
from .issue_trackers import register_issue_tracker_tools
from .wafs import register_waf_tools
from .roles import register_role_tools
from .agents import register_agent_tools
from .excluded_hours import register_excluded_hours_tools

__all__ = [
    "register_target_tools",
    "register_scan_tools",
    "register_vulnerability_tools",
    "register_result_tools",
    "register_report_tools",
    "register_user_tools",
    "register_group_tools",
    "register_scanning_profile_tools",
    "register_worker_tools",
    "register_issue_tracker_tools",
    "register_waf_tools",
    "register_role_tools",
    "register_agent_tools",
    "register_excluded_hours_tools",
]
