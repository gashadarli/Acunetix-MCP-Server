"""Worker management MCP tools."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix


def register_worker_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_workers() -> Dict[str, Any]:
        """
        Get a list of all registered Workers (distributed scanning engines).
        """
        return await acunetix.get("/workers")

    @mcp.tool()
    async def get_worker(worker_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Worker.
        """
        return await acunetix.get(f"/workers/{worker_id}")

    @mcp.tool()
    async def delete_worker(worker_id: str) -> Dict[str, Any]:
        """
        Delete/unregister a Worker.
        """
        return await acunetix.delete(f"/workers/{worker_id}")

    @mcp.tool()
    async def authorize_worker(worker_id: str) -> Dict[str, Any]:
        """
        Authorize a pending Worker to start scanning.
        """
        return await acunetix.post(f"/workers/{worker_id}/authorize", body={})

    @mcp.tool()
    async def reject_worker(worker_id: str) -> Dict[str, Any]:
        """
        Reject a pending Worker registration request.
        """
        return await acunetix.post(f"/workers/{worker_id}/reject", body={})

    @mcp.tool()
    async def check_worker(worker_id: str) -> Dict[str, Any]:
        """
        Check the connection status and health of a Worker.
        """
        return await acunetix.post(f"/workers/{worker_id}/check", body={})

    @mcp.tool()
    async def upgrade_worker(worker_id: str) -> Dict[str, Any]:
        """
        Upgrade a Worker to the latest build version.
        """
        return await acunetix.post(f"/workers/{worker_id}/upgrade", body={})

    @mcp.tool()
    async def rename_worker(
        worker_id: str,
        name: str,
    ) -> Dict[str, Any]:
        """
        Rename a Worker.
        """
        return await acunetix.post(
            f"/workers/{worker_id}/rename",
            body={"description": name},
        )

    @mcp.tool()
    async def delete_worker_ignore_errors(worker_id: str) -> Dict[str, Any]:
        """
        Clear/ignore error flags on a Worker.
        """
        return await acunetix.delete(f"/workers/{worker_id}/ignore_errors")
