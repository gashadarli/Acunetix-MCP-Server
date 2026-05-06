"""Call key read-only Acunetix MCP tools over HTTP and print a safe summary."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from fastmcp import Client


READ_ONLY_TOOLS = [
    "acunetix_health",
    "list_target_groups",
    "list_targets",
    "list_scans",
]


def _count_items(data: Any) -> int | None:
    if not isinstance(data, dict):
        return None
    for key in ("groups", "targets", "scans", "vulnerabilities", "reports"):
        value = data.get(key)
        if isinstance(value, list):
            return len(value)
    return None


def _safe_summary(name: str, result: Any) -> dict[str, Any]:
    structured = getattr(result, "structured_content", None)
    if structured is None and hasattr(result, "data"):
        structured = result.data
    if structured is None:
        try:
            structured = json.loads(result.content[0].text)
        except Exception:
            structured = result

    if not isinstance(structured, dict):
        return {"tool": name, "success": False, "result_type": type(structured).__name__}

    data = structured.get("data")
    summary: dict[str, Any] = {
        "tool": name,
        "success": structured.get("success"),
        "status_code": structured.get("status_code") or structured.get("api_status_code"),
    }
    count = _count_items(data)
    if count is not None:
        summary["item_count"] = count
    if not structured.get("success"):
        error = structured.get("error")
        if isinstance(error, dict):
            summary["error"] = error.get("message")
        else:
            summary["error"] = error
    return summary


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080/mcp")
    args = parser.parse_args()

    async with Client(args.url) as client:
        tools = await client.list_tools()
        print(json.dumps({"tool_count": len(tools), "tools": sorted(t.name for t in tools)}))
        for tool_name in READ_ONLY_TOOLS:
            result = await client.call_tool(tool_name, {})
            print(json.dumps(_safe_summary(tool_name, result), sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
