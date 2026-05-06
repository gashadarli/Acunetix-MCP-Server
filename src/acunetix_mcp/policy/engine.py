"""Policy checks for Acunetix MCP action tools."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from urllib.parse import urlsplit

from ..config import Settings, load_settings


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""


class PolicyEngine:
    """Enforces read-only mode, confirmation, and target allowlists."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()

    def check_read(self) -> PolicyDecision:
        return PolicyDecision(True, "read-only action")

    def check_action(
        self,
        action: str,
        *,
        confirmed: bool = False,
        target_id: str | None = None,
        address: str | None = None,
    ) -> PolicyDecision:
        if self.settings.read_only:
            return PolicyDecision(
                False,
                f"{action} is blocked because ACUNETIX_READ_ONLY is enabled.",
            )

        if self.settings.require_confirmation and not confirmed:
            return PolicyDecision(
                False,
                f"{action} requires confirmation=true.",
            )

        if (target_id or address) and not self.is_target_allowed(target_id, address):
            return PolicyDecision(
                False,
                f"{action} is blocked by ACUNETIX_TARGET_ALLOWLIST.",
            )

        return PolicyDecision(True, "allowed")

    def is_target_allowed(
        self,
        target_id: str | None = None,
        address: str | None = None,
    ) -> bool:
        allowlist = self.settings.allowed_targets
        if not allowlist:
            return True

        candidates: set[str] = set()
        if target_id:
            candidates.add(target_id)
        if address:
            candidates.add(address)
            parsed = urlsplit(address)
            if parsed.netloc:
                candidates.add(parsed.netloc)
                candidates.add(parsed.hostname or "")

        for candidate in candidates:
            if not candidate:
                continue
            for pattern in allowlist:
                if fnmatch(candidate, pattern):
                    return True
        return False


def policy_error(decision: PolicyDecision) -> dict[str, object]:
    return {
        "success": False,
        "error": {
            "message": decision.reason,
            "type": "PolicyDenied",
        },
    }
