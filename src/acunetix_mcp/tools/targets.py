"""Target and target group MCP tools."""

from __future__ import annotations

from typing import Any

import fastmcp

from ..audit import audit_event
from ..client import acunetix
from ..policy import PolicyEngine, policy_error
from .common import validate_limit, validate_url, validate_uuid


def register_target_tools(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool(name="list_targets")
    async def list_targets(
        search: str | None = None,
        limit: int | None = 50,
        offset: str | None = None,
    ) -> dict[str, Any]:
        """List Acunetix targets with optional text search and pagination."""
        params: dict[str, Any] = {"l": validate_limit(limit)}
        if search:
            params["q"] = f"text:{search}"
        if offset:
            params["c"] = offset
        return await acunetix.get("/targets", params=params)

    @mcp.tool(name="get_target")
    async def get_target(target_id: str) -> dict[str, Any]:
        """Get a single Acunetix target by target UUID."""
        error = validate_uuid(target_id, "target_id")
        if error:
            return error
        return await acunetix.get(f"/targets/{target_id}")

    @mcp.tool(name="list_target_groups")
    async def list_target_groups(
        search: str | None = None,
        limit: int | None = 50,
        offset: str | None = None,
    ) -> dict[str, Any]:
        """List Acunetix target groups with optional text search."""
        params: dict[str, Any] = {"l": validate_limit(limit)}
        if search:
            params["q"] = f"text:{search}"
        if offset:
            params["c"] = offset
        return await acunetix.get("/target_groups", params=params)

    @mcp.tool(name="get_target_group")
    async def get_target_group(group_id: str) -> dict[str, Any]:
        """Get a single Acunetix target group by group UUID."""
        error = validate_uuid(group_id, "group_id")
        if error:
            return error
        return await acunetix.get(f"/target_groups/{group_id}")

    @mcp.tool(name="create_target")
    async def create_target(
        address: str,
        description: str | None = None,
        criticality: int = 10,
        confirmation: bool = False,
    ) -> dict[str, Any]:
        """Create an Acunetix target after policy and confirmation checks."""
        url_error = validate_url(address)
        if url_error:
            return url_error

        if criticality not in {0, 10, 20, 30, 40}:
            return {
                "success": False,
                "error": {
                    "message": "criticality must be one of 0, 10, 20, 30, 40.",
                    "type": "ValidationError",
                },
            }

        policy = PolicyEngine()
        decision = policy.check_action(
            "create_target",
            confirmed=confirmation,
            address=address,
        )
        audit_event(
            "create_target",
            allowed=decision.allowed,
            reason=decision.reason,
            details={"address": address, "criticality": criticality},
        )
        if not decision.allowed:
            return policy_error(decision)

        body: dict[str, Any] = {
            "address": address,
            "type": "default",
            "criticality": criticality,
        }
        if description:
            body["description"] = description
        return await acunetix.post("/targets", body=body)
