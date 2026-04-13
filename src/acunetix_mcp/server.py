"""
Acunetix MCP Server — main entry point.

Transport modes
---------------
stdio (default) — MCP client launches this server as a subprocess and
    communicates via stdin/stdout JSON-RPC. Use this with:
    - OpenClaw
    - Claude Desktop
    - Cursor, Zed, VS Code MCP extensions
    - Any local MCP client

HTTP (--http flag) — server listens on a TCP port using the streamable-HTTP
    MCP transport. Use this with:
    - Docker deployments
    - Remote/shared setups
    - Clients that only support URL-based MCP config

Usage
-----
    # stdio (default — for MCP clients that launch a subprocess)
    python -m acunetix_mcp.server

    # HTTP transport (e.g. inside Docker)
    python -m acunetix_mcp.server --http
    python -m acunetix_mcp.server --http --port 8080
"""

import logging
import sys

from fastmcp import FastMCP

from .config import config
from .tools import register_all_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,   # never pollute stdout — that is used for MCP JSON-RPC
)
logger = logging.getLogger("acunetix-mcp")


def create_server() -> FastMCP:
    """Create and return the configured MCP server instance."""

    mcp = FastMCP(
        name="acunetix-mcp",
        instructions="""
You are connected to the Acunetix Web Vulnerability Scanner API via the
acunetix-mcp server. All tool names are prefixed with acunetix__ so they
are easy to identify and never conflict with other MCP servers.

Core capabilities
-----------------
TARGETS
  acunetix__list_targets          — list / search scan targets
  acunetix__get_target            — detailed info for one target
  acunetix__add_target            — create a new scan target

SCANS
  acunetix__list_scans            — list scans (filter by target/status)
  acunetix__start_scan            — start a scan on a target
  acunetix__get_scan_status       — poll status of a running/completed scan
  acunetix__abort_scan            — stop a running scan
  acunetix__get_scan_results      — scan result history for a scan
  acunetix__list_scanning_profiles — show available scan profile IDs/names

VULNERABILITIES
  acunetix__list_vulnerabilities       — list found vulnerabilities
  acunetix__get_vulnerability          — detailed finding info
  acunetix__update_vulnerability_status — mark open/fixed/false_positive/ignored
  acunetix__list_vulnerability_types   — breakdown by type

REPORTS
  acunetix__list_report_templates — available report format templates
  acunetix__generate_report       — create a PDF/HTML report
  acunetix__list_reports          — show generated reports
  acunetix__get_report            — report details + download descriptor

RESULTS
  acunetix__get_scan_result       — one scan session's details
  acunetix__get_scan_statistics   — vuln counts, URLs scanned, duration

Typical workflows
-----------------
Inventory query:     list_targets → get_target
Launch & monitor:    add_target → start_scan → get_scan_status (poll)
Triage findings:     list_scans → get_scan_results → list_vulnerabilities → get_vulnerability
Generate report:     list_report_templates → generate_report → get_report
""",
    )

    # Register all namespaced tools
    register_all_tools(mcp)

    logger.info("Acunetix MCP Server ready")
    return mcp


# Module-level singleton — importable for testing
mcp = create_server()


def main() -> None:
    """Entry point registered in pyproject.toml."""
    use_http = "--http" in sys.argv

    # Parse optional --port argument
    port = config.MCP_SERVER_PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        try:
            port = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            logger.error("--port requires an integer argument")
            sys.exit(1)

    if use_http:
        logger.info(
            "Starting Acunetix MCP Server — HTTP transport on %s:%d",
            config.MCP_SERVER_HOST,
            port,
        )
        mcp.run(
            transport="streamable-http",
            host=config.MCP_SERVER_HOST,
            port=port,
        )
    else:
        logger.info("Starting Acunetix MCP Server — stdio transport")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
