"""Scan MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any

import fastmcp

from ..audit import audit_event
from ..client import acunetix
from ..config import load_settings
from ..policy import PolicyEngine, policy_error
from .common import validate_limit, validate_uuid


PROFILE_FULL_SCAN = "11111111-1111-1111-1111-111111111111"
VALID_SCAN_STATUSES = {
    "processing",
    "scheduled",
    "running",
    "pausing",
    "paused",
    "completed",
    "aborted",
    "failed",
    "empty",
}

_scan_start_lock = asyncio.Lock()
_scan_start_semaphore: asyncio.Semaphore | None = None
_scan_start_limit: int | None = None


async def _scan_semaphore() -> asyncio.Semaphore:
    global _scan_start_limit, _scan_start_semaphore
    settings = load_settings()
    async with _scan_start_lock:
        if (
            _scan_start_semaphore is None
            or _scan_start_limit != settings.max_concurrent_scan_starts
        ):
            _scan_start_limit = settings.max_concurrent_scan_starts
            _scan_start_semaphore = asyncio.Semaphore(_scan_start_limit)
        return _scan_start_semaphore


def _target_address_from_response(response: dict[str, Any]) -> str | None:
    data = response.get("data")
    if isinstance(data, dict):
        address = data.get("address")
        return str(address) if address else None
    return None


async def _scan_target_id(scan_id: str) -> str | None:
    response = await acunetix.get(f"/scans/{scan_id}")
    data = response.get("data")
    if isinstance(data, dict):
        target_id = data.get("target_id")
        if target_id:
            return str(target_id)
        target = data.get("target")
        if isinstance(target, dict) and target.get("target_id"):
            return str(target["target_id"])
    return None


def register_scan_tools(mcp: fastmcp.FastMCP) -> None:
    @mcp.tool(name="list_scans")
    async def list_scans(
        target_id: str | None = None,
        status: str | None = None,
        limit: int | None = 20,
        offset: str | None = None,
    ) -> dict[str, Any]:
        """List Acunetix scans, optionally filtered by target UUID or status."""
        query_parts: list[str] = []
        if target_id:
            error = validate_uuid(target_id, "target_id")
            if error:
                return error
            query_parts.append(f"target_id:{target_id}")
        if status:
            if status not in VALID_SCAN_STATUSES:
                return {
                    "success": False,
                    "error": {
                        "message": f"status must be one of {sorted(VALID_SCAN_STATUSES)}.",
                        "type": "ValidationError",
                    },
                }
            query_parts.append(f"status:{status}")

        params: dict[str, Any] = {"l": validate_limit(limit)}
        if query_parts:
            params["q"] = ";".join(query_parts)
        if offset:
            params["c"] = offset
        return await acunetix.get("/scans", params=params)

    @mcp.tool(name="get_scan_status")
    async def get_scan_status(scan_id: str) -> dict[str, Any]:
        """Get status, progress, and latest result metadata for a scan UUID."""
        error = validate_uuid(scan_id, "scan_id")
        if error:
            return error
        return await acunetix.get(f"/scans/{scan_id}")

    @mcp.tool(name="list_scanning_profiles")
    async def list_scanning_profiles() -> dict[str, Any]:
        """List Acunetix scanning profiles that can be used with start_scan."""
        return await acunetix.get("/scanning_profiles")

    @mcp.tool(name="start_scan")
    async def start_scan(
        target_id: str,
        profile_id: str | None = None,
        confirmation: bool = False,
    ) -> dict[str, Any]:
        """Start a scan on a target after policy, allowlist, and confirmation checks."""
        error = validate_uuid(target_id, "target_id")
        if error:
            return error
        if profile_id:
            profile_error = validate_uuid(profile_id, "profile_id")
            if profile_error:
                return profile_error

        policy = PolicyEngine()
        preflight = policy.check_action(
            "start_scan",
            confirmed=confirmation,
        )
        if not preflight.allowed:
            audit_event(
                "start_scan",
                allowed=preflight.allowed,
                reason=preflight.reason,
                details={
                    "target_id": target_id,
                    "profile_id": profile_id or PROFILE_FULL_SCAN,
                },
            )
            return policy_error(preflight)

        target_response = await acunetix.get(f"/targets/{target_id}")
        target_address = _target_address_from_response(target_response)
        decision = policy.check_action(
            "start_scan",
            confirmed=confirmation,
            target_id=target_id,
            address=target_address,
        )
        audit_event(
            "start_scan",
            allowed=decision.allowed,
            reason=decision.reason,
            details={
                "target_id": target_id,
                "target_address": target_address,
                "profile_id": profile_id or PROFILE_FULL_SCAN,
            },
        )
        if not decision.allowed:
            return policy_error(decision)
        if not target_response.get("success"):
            return target_response

        body: dict[str, Any] = {
            "target_id": target_id,
            "profile_id": profile_id or PROFILE_FULL_SCAN,
            "schedule": {
                "disable": False,
                "start_date": None,
                "time_sensitive": False,
            },
        }
        semaphore = await _scan_semaphore()
        async with semaphore:
            return await acunetix.post("/scans", body=body)

    @mcp.tool(name="stop_scan")
    async def stop_scan(scan_id: str, confirmation: bool = False) -> dict[str, Any]:
        """Stop a running Acunetix scan after policy and confirmation checks."""
        error = validate_uuid(scan_id, "scan_id")
        if error:
            return error

        policy = PolicyEngine()
        preflight = policy.check_action("stop_scan", confirmed=confirmation)
        if not preflight.allowed:
            audit_event(
                "stop_scan",
                allowed=preflight.allowed,
                reason=preflight.reason,
                details={"scan_id": scan_id},
            )
            return policy_error(preflight)

        target_id = await _scan_target_id(scan_id)
        decision = policy.check_action(
            "stop_scan",
            confirmed=confirmation,
            target_id=target_id,
        )
        audit_event(
            "stop_scan",
            allowed=decision.allowed,
            reason=decision.reason,
            details={"scan_id": scan_id, "target_id": target_id},
        )
        if not decision.allowed:
            return policy_error(decision)
        return await acunetix.post(f"/scans/{scan_id}/abort")
