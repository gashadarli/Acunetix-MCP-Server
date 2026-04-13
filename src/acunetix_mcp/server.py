"""
Acunetix MCP Server - Main entry point.

This server exposes the full Acunetix Scanner API as MCP tools,
allowing AI assistants (Claude, ChatGPT, Gemini, OpenClaw) to
manage Acunetix scans, targets, vulnerabilities, and reports.
"""

import logging

import uvicorn
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.routing import Route

from .config import config
from .tools import (
    register_target_tools,
    register_scan_tools,
    register_vulnerability_tools,
    register_result_tools,
    register_report_tools,
    register_user_tools,
    register_group_tools,
    register_scanning_profile_tools,
    register_worker_tools,
    register_issue_tracker_tools,
    register_waf_tools,
    register_role_tools,
    register_agent_tools,
    register_excluded_hours_tools,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("acunetix-mcp")


def create_server() -> FastMCP:
    """Create and configure the MCP server with all Acunetix tools."""

    mcp = FastMCP(
        name="Acunetix MCP Server",
        instructions="""
You are connected to the Acunetix Web Vulnerability Scanner API.

You can manage:
- **Targets**: Web applications and networks to scan
- **Scans**: Schedule, run, abort, and manage vulnerability scans
- **Vulnerabilities**: View, filter, and update vulnerability status
- **Reports**: Generate PDF/HTML reports for compliance and sharing
- **Users & Groups**: Manage access control
- **Scanning Profiles**: Configure what vulnerabilities to check
- **Workers**: Manage distributed scanning engines
- **Issue Trackers**: Integrate with Jira, GitHub, GitLab, Azure DevOps
- **WAFs**: Export findings to WAF products
- **Scan Results**: Deep dive into crawl data, technologies, statistics

Base URL: """ + config.ACUNETIX_BASE_URL + """
        """,
    )

    # Register all tool modules
    register_target_tools(mcp)
    register_scan_tools(mcp)
    register_vulnerability_tools(mcp)
    register_result_tools(mcp)
    register_report_tools(mcp)
    register_user_tools(mcp)
    register_group_tools(mcp)
    register_scanning_profile_tools(mcp)
    register_worker_tools(mcp)
    register_issue_tracker_tools(mcp)
    register_waf_tools(mcp)
    register_role_tools(mcp)
    register_agent_tools(mcp)
    register_excluded_hours_tools(mcp)

    logger.info("Acunetix MCP Server initialized")
    logger.info(f"Acunetix Base URL: {config.ACUNETIX_BASE_URL}")
    logger.info(f"SSL Verification: {config.VERIFY_SSL}")

    return mcp


# Create the global MCP server instance
mcp = create_server()


async def health_endpoint(request):
    """Health check endpoint for Docker and monitoring."""
    tool_count = len(await mcp.list_tools())
    return JSONResponse({
        "status": "healthy",
        "server": "Acunetix MCP Server",
        "version": "1.0.0",
        "tools": tool_count,
    })


def main():
    """Entry point for running the MCP server."""
    logger.info(
        f"Starting Acunetix MCP Server on {config.MCP_SERVER_HOST}:{config.MCP_SERVER_PORT}"
    )

    # Get the Starlette ASGI app from FastMCP
    app = mcp.http_app(transport="streamable-http")

    # Add custom health endpoint for Docker healthcheck
    app.add_route("/health", health_endpoint, methods=["GET"])

    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.MCP_SERVER_HOST,
        port=config.MCP_SERVER_PORT,
        log_level="info",
        timeout_graceful_shutdown=2,
    )


if __name__ == "__main__":
    main()
