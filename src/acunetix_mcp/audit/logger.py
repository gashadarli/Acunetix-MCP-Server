"""Minimal audit logging for state-changing Acunetix MCP tools."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from ..config import load_settings, mask_secret

logger = logging.getLogger("acunetix_mcp.audit")


def _redact(value: Any, secret: str | None) -> Any:
    if isinstance(value, str):
        return mask_secret(value, secret)
    if isinstance(value, list):
        return [_redact(item, secret) for item in value]
    if isinstance(value, tuple):
        return [_redact(item, secret) for item in value]
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in {"api_key", "x-auth", "authorization"}:
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = _redact(item, secret)
        return redacted
    return value


def audit_event(
    action: str,
    *,
    allowed: bool,
    reason: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Write one structured audit event to stderr and optional JSONL file."""
    settings = load_settings()
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "allowed": allowed,
        "reason": reason,
        "details": _redact(details or {}, settings.acunetix_api_key),
    }

    logger.info("audit %s", json.dumps(event, sort_keys=True))

    if not settings.audit_log_path:
        return

    try:
        path = Path(settings.audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")
    except OSError as exc:
        logger.warning("failed to write audit log: %s", exc)
