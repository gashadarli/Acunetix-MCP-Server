from acunetix_mcp.config import Settings
from acunetix_mcp.policy import PolicyEngine


def test_read_only_blocks_action():
    policy = PolicyEngine(Settings(read_only=True))

    decision = policy.check_action("start_scan", confirmed=True)

    assert decision.allowed is False
    assert "READ_ONLY" in decision.reason


def test_confirmation_is_required():
    policy = PolicyEngine(Settings(read_only=False, require_confirmation=True))

    decision = policy.check_action("stop_scan", confirmed=False)

    assert decision.allowed is False
    assert "confirmation=true" in decision.reason


def test_allowlist_accepts_hostname_pattern():
    policy = PolicyEngine(
        Settings(
            read_only=False,
            require_confirmation=False,
            allowed_targets=("*.example.com",),
        )
    )

    decision = policy.check_action(
        "create_target",
        address="https://app.example.com",
    )

    assert decision.allowed is True


def test_allowlist_rejects_unknown_target():
    policy = PolicyEngine(
        Settings(
            read_only=False,
            require_confirmation=False,
            allowed_targets=("11111111-1111-1111-1111-111111111111",),
        )
    )

    decision = policy.check_action(
        "start_scan",
        target_id="22222222-2222-2222-2222-222222222222",
    )

    assert decision.allowed is False
