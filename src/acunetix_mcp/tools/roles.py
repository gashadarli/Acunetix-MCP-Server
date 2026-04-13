"""Role and permissions management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_role_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_roles(
        query: Optional[str] = None,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        extended: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get all Roles defined in the system.
        Roles define what actions users can perform.
        """
        return await acunetix.get(
            "/roles",
            params={"q": query, "s": sort, "c": cursor, "l": limit, "extended": extended},
        )

    @mcp.tool()
    async def create_role(
        name: str,
        permissions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Role with specific permissions.
        permissions: List of permission names (get from get_permissions).
        """
        body: Dict[str, Any] = {"name": name}
        if permissions:
            body["permissions"] = permissions
        return await acunetix.post("/roles", body=body)

    @mcp.tool()
    async def get_role(role_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Role.
        """
        return await acunetix.get(f"/roles/{role_id}")

    @mcp.tool()
    async def update_role(
        role_id: str,
        name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Modify an existing Role.
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if permissions is not None:
            body["permissions"] = permissions
        return await acunetix.patch(f"/roles/{role_id}", body=body)

    @mcp.tool()
    async def delete_role(
        role_id: str,
        force_delete: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete a Role.
        force_delete: If True, removes role from all user groups using it.
        """
        return await acunetix.delete(f"/roles/{role_id}")

    @mcp.tool()
    async def get_permissions() -> Dict[str, Any]:
        """
        Get all available Permissions that can be assigned to Roles.
        Use these permission names when creating or updating roles.
        """
        return await acunetix.get("/roles/permissions")
