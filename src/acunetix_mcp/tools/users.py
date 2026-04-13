"""User management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_user_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_users(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of all Users in the Acunetix system.
        """
        return await acunetix.get(
            "/users",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def add_user(
        email: str,
        first_name: str,
        last_name: str,
        role: Optional[str] = None,
        password: Optional[str] = None,
        send_email: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new User.
        email: User's email address (used as login)
        first_name, last_name: User's name
        role: 'administrator', 'tester'
        send_email: Whether to send invitation email
        """
        body: Dict[str, Any] = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
        if role:
            body["role"] = role
        if password:
            body["password"] = password

        return await acunetix.post(
            "/users",
            body=body,
            params={"send_email": send_email},
        )

    @mcp.tool()
    async def get_user(user_id: str) -> Dict[str, Any]:
        """
        Get details of a specific User.
        """
        return await acunetix.get(f"/users/{user_id}")

    @mcp.tool()
    async def update_user(
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Modify a User's properties.
        """
        body: Dict[str, Any] = {}
        if email:
            body["email"] = email
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if role:
            body["role"] = role
        if password:
            body["password"] = password
        return await acunetix.patch(f"/users/{user_id}", body=body)

    @mcp.tool()
    async def remove_user(user_id: str) -> Dict[str, Any]:
        """
        Delete a specific User.
        """
        return await acunetix.delete(f"/users/{user_id}")

    @mcp.tool()
    async def remove_users(user_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple Users at once.
        """
        return await acunetix.post(
            "/users/delete",
            body={"user_id_list": user_ids},
        )

    @mcp.tool()
    async def enable_users(user_ids: List[str]) -> Dict[str, Any]:
        """
        Enable one or more Users (allow login).
        """
        return await acunetix.post(
            "/users/enable",
            body={"user_id_list": user_ids},
        )

    @mcp.tool()
    async def disable_users(user_ids: List[str]) -> Dict[str, Any]:
        """
        Disable one or more Users (prevent login without deleting).
        """
        return await acunetix.post(
            "/users/disable",
            body={"user_id_list": user_ids},
        )
