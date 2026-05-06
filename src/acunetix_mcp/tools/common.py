"""Shared validation helpers for MCP tools."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit


UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def validate_uuid(value: str, field_name: str) -> dict[str, Any] | None:
    if not value or not UUID_RE.match(value):
        return {
            "success": False,
            "error": {
                "message": f"{field_name} must be a UUID.",
                "type": "ValidationError",
            },
        }
    return None


def validate_limit(limit: int | None, *, default: int = 50, maximum: int = 100) -> int:
    if limit is None:
        return default
    return max(1, min(int(limit), maximum))


def validate_url(address: str) -> dict[str, Any] | None:
    parsed = urlsplit(address or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "success": False,
            "error": {
                "message": "address must be an absolute http or https URL.",
                "type": "ValidationError",
            },
        }
    return None
