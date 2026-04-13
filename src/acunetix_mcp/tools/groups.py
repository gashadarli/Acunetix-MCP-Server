"""Target Group and User Group management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_group_tools(mcp: fastmcp.FastMCP):

    # ─── Target Groups ───────────────────────────────────────────────────────

    @mcp.tool()
    async def get_target_groups(
        query: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all Target Groups. Target groups are used to organize targets.
        """
        return await acunetix.get(
            "/target_groups",
            params={"q": query, "c": cursor, "l": limit, "s": sort},
        )

    @mcp.tool()
    async def add_target_group(
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Target Group.
        """
        body: Dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        return await acunetix.post("/target_groups", body=body)

    @mcp.tool()
    async def get_target_group(group_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Target Group.
        """
        return await acunetix.get(f"/target_groups/{group_id}")

    @mcp.tool()
    async def update_target_group(
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Modify a Target Group (rename or change description).
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        return await acunetix.patch(f"/target_groups/{group_id}", body=body)

    @mcp.tool()
    async def delete_target_group(group_id: str) -> Dict[str, Any]:
        """
        Delete a specific Target Group.
        """
        return await acunetix.delete(f"/target_groups/{group_id}")

    @mcp.tool()
    async def delete_target_groups(group_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple Target Groups at once.
        """
        return await acunetix.post(
            "/target_groups/delete",
            body={"group_id_list": group_ids},
        )

    @mcp.tool()
    async def get_targets_in_group(group_id: str) -> Dict[str, Any]:
        """
        Get all Targets in a Target Group.
        """
        return await acunetix.get(f"/target_groups/{group_id}/targets")

    @mcp.tool()
    async def assign_targets_to_group(
        group_id: str,
        target_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Assign one or more Targets to a Target Group.
        """
        return await acunetix.post(
            f"/target_groups/{group_id}/targets",
            body={"target_id_list": target_ids},
        )

    @mcp.tool()
    async def update_targets_in_group(
        group_id: str,
        target_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Update (replace) the Targets list in a Target Group.
        """
        return await acunetix.patch(
            f"/target_groups/{group_id}/targets",
            body={"target_id_list": target_ids},
        )

    # ─── User Groups ─────────────────────────────────────────────────────────

    @mcp.tool()
    async def get_user_groups(
        query: Optional[str] = None,
        sort: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        extended: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get all User Groups. User groups are used to manage access control.
        """
        return await acunetix.get(
            "/user_groups",
            params={"q": query, "s": sort, "c": cursor, "l": limit, "extended": extended},
        )

    @mcp.tool()
    async def create_user_group(
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new User Group.
        """
        body: Dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        return await acunetix.post("/user_groups", body=body)

    @mcp.tool()
    async def get_user_group(user_group_id: str) -> Dict[str, Any]:
        """
        Get details of a specific User Group.
        """
        return await acunetix.get(f"/user_groups/{user_group_id}")

    @mcp.tool()
    async def update_user_group(
        user_group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Modify a User Group.
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if description:
            body["description"] = description
        return await acunetix.patch(f"/user_groups/{user_group_id}", body=body)

    @mcp.tool()
    async def remove_user_group(
        user_group_id: str,
        force_delete: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete a User Group.
        force_delete: If True, removes all user connections to this group.
        """
        return await acunetix.delete(f"/user_groups/{user_group_id}")

    @mcp.tool()
    async def add_users_to_user_group(
        user_group_id: str,
        user_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Add Users to a User Group.
        """
        return await acunetix.post(
            f"/user_groups/{user_group_id}/users",
            body={"user_id_list": user_ids},
        )

    @mcp.tool()
    async def remove_users_from_user_group(
        user_group_id: str,
        user_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Remove Users from a User Group.
        """
        return await acunetix.delete(
            f"/user_groups/{user_group_id}/users",
            body={"user_id_list": user_ids},
        )

    @mcp.tool()
    async def get_user_group_role_mappings(user_group_id: str) -> Dict[str, Any]:
        """
        List all Role Mappings for a User Group.
        """
        return await acunetix.get(f"/user_groups/{user_group_id}/roles")

    @mcp.tool()
    async def add_role_mappings_to_user_group(
        user_group_id: str,
        role_mappings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Add Role Mappings to a User Group.
        role_mappings: List of objects with 'role_id' and optionally 'target_group_id'
        """
        return await acunetix.post(
            f"/user_groups/{user_group_id}/roles",
            body={"role_mapping_list": role_mappings},
        )

    @mcp.tool()
    async def remove_role_mappings_from_user_group(
        user_group_id: str,
        role_mapping_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Remove Role Mappings from a User Group.
        """
        return await acunetix.delete(
            f"/user_groups/{user_group_id}/roles",
            body={"role_mapping_id_list": role_mapping_ids},
        )
