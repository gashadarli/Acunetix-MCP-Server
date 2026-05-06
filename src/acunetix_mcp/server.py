"""Acunetix MCP server entrypoint."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Literal

from fastmcp import FastMCP
from starlette.responses import JSONResponse

from .config import load_settings
from .prompts import register_prompts
from .resources import register_resources
from .tools import register_all_tools


logger = logging.getLogger("acunetix_mcp")


def configure_logging() -> None:
    settings = load_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


def create_server() -> FastMCP:
    """Create the model-agnostic FastMCP server and register typed tools."""
    mcp = FastMCP(
        name="acunetix-mcp",
        instructions=(
            "Use these typed tools to interact with Acunetix safely. "
            "Read-only tools can inspect targets, target groups, scans, "
            "vulnerabilities, and reports. Action tools require policy checks "
            "and explicit confirmation."
        ),
        strict_input_validation=True,
        mask_error_details=True,
    )

    @mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health_route(request):  # noqa: ANN001 - Starlette request type is not needed here.
        return JSONResponse({"status": "ok", "service": "acunetix-mcp"})

    register_all_tools(mcp)
    register_prompts(mcp)
    register_resources(mcp)
    return mcp


mcp = create_server()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Acunetix MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http"],
        default=None,
        help="MCP transport to use. Defaults to MCP_TRANSPORT or stdio.",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Compatibility alias for --transport http.",
    )
    parser.add_argument("--host", default=None, help="HTTP bind host.")
    parser.add_argument("--port", type=int, default=None, help="HTTP bind port.")
    return parser.parse_args(argv)


def _resolve_transport(args: argparse.Namespace) -> Literal["stdio", "http"]:
    settings = load_settings()
    if args.http:
        return "http"
    transport = (args.transport or settings.mcp_transport or "stdio").lower()
    if transport in {"http", "streamable-http"}:
        return "http"
    return "stdio"


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = _parse_args(argv)
    settings = load_settings()
    transport = _resolve_transport(args)

    if transport == "http":
        host = args.host or settings.mcp_server_host
        port = args.port or settings.mcp_server_port
        logger.info("Starting Acunetix MCP Server with HTTP transport on %s:%d", host, port)
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            path="/mcp",
            show_banner=False,
        )
        return

    logger.info("Starting Acunetix MCP Server with stdio transport")
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
