"""
Deep billing service-level integration tests.

These tests exercise the real service.py state machine logic directly —
NOT via HTTP contract mocks. They cover:
  - All valid state transition paths
  - Invalid transition guards (ValueError)
  - Cancelled-is-terminal invariant
  - Trial expiry logic (_apply_trial_expiry) with monkeypatched _now()
  - BILLING_TRIAL_AUTO_ACTIVATE auto-activation path
  - Trial with missing trial_ends_at → suspended (fail-safe)
  - PLAN_RANK-based upgrade (immediate) vs downgrade (next_period) auto logic
  - explicit effective=immediate / next_period / invalid
  - Period rollover (_apply_period_rollover) applied by get_tenant_subscription
  - assert_billing_write_allowed: trial/active pass, suspended/cancelled raise 403
  - assert_quota_with_increment: within limit passes, over limit raises 403
  - get_tenant_billing_state: billing_state="read_write"/"read_only"
  - Multi-tenant state isolation: tenant A does not affect tenant B
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.modules.billing import service as billing_service
from app.modules.billing.service import (
    assert_billing_write_allowed,
    assert_quota_with_increment,
    change_subscription_plan,
    clear_billing_state,
    ensure_tenant_subscription,
    get_tenant_billing_state,
    get_tenant_subscription,
    transition_subscription_status,
)
from app.modules.plans.service import get_plan_by_code
from app.modules.quotas.service import update_plan_quotas
from tests.conftest import client


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _provision(suffix: str, plan: str = "free") -> int:
    """Provision a new tenant via HTTP; returns numeric tenant_id."""
    r = client.post(
        "/api/platform/tenants",
        headers={"Idempotency-Key": f"billing-svc-int-{suffix}"},
        json={
            "tenant_name": f"Billing SvcInt {suffix}",
            "admin_login": f"svcint.{suffix}",
            "admin_password": "StrongPass123!",
            "plan_code": plan,
        },
    )
    assert r.status_code == 201, r.text
    return int(r.json()["tenant"]["id"])


@pytest.fixture(autouse=True)
def _clean_billing_state():
    """Clear billing in-memory state before each test for full isolation."""
    clear_billing_state()
    yield
    clear_billing_state()


# ─── Category 1: Valid state-machine transitions ──────────────────────────────

class TestValidTransitions:
    def test_trial_to_active(self):
        tid = _provision("valid-t2a")
        sub = transition_subscription_status(tid, "active")
        assert sub["status"] == "active"

    def test_trial_to_suspended(self):
        tid = _provision("valid-t2s")
        sub = transition_subscription_status(tid, "suspended")
        assert sub["status"] == "suspended"

    def test_trial_to_cancelled(self):
        tid = _provision("valid-t2c")
        sub = transition_subscription_status(tid, "cancelled")
        assert sub["status"] == "cancelled"

    def test_active_to_suspended(self):
        tid = _provision("valid-a2s")
        transition_subscription_status(tid, "active")
        sub = transition_subscription_status(tid, "suspended")
        assert sub["status"] == "suspended"

    def test_suspended_to_active(self):
        tid = _provision("valid-s2a")
        transition_subscription_status(tid, "suspended")
        sub = transition_subscription_status(tid, "active")
        assert sub["status"] == "active"

    def test_active_to_cancelled(self):
        tid = _provision("valid-a2c")
        transition_subscription_status(tid, "active")
        sub = transition_subscription_status(tid, "cancelled")
        assert sub["status"] == "cancelled"

    def test_suspended_to_cancelled(self):
        tid = _provision("valid-s2c")
        transition_subscription_status(tid, "suspended")
        sub = transition_subscription_status(tid, "cancelled")
        assert sub["status"] == "cancelled"

    def test_full_lifecycle_trial_active_suspended_active_cancelled(self):
        """Full lifecycle traversal: trial→active→suspended→active→cancelled."""
        tid = _provision("valid-lifecycle")
        transition_subscription_status(tid, "active")
        transition_subscription_status(tid, "suspended")
        transition_subscription_status(tid, "active")
        final = transition_subscription_status(tid, "cancelled")
        assert final["status"] == "cancelled"

    def test_idempotent_same_status(self):
        """Transitioning to the current status is idempotent (no ValueError)."""
        tid = _provision("valid-idem")
        sub = transition_subscription_status(tid, "trial")
        assert sub["status"] == "trial"


# ─── Category 2: Invalid transition guards ───────────────────────────────────

class TestInvalidTransitions:
    def test_cancelled_to_active_raises(self):
        """Cancelled is terminal — attempting to reactivate raises ValueError."""
        tid = _provision("guard-c2a")
        transition_subscription_status(tid, "cancelled")
        with pytest.raises(ValueError) as exc_info:
            transition_subscription_status(tid, "active")
        msg = str(exc_info.value).lower()
        # Either "invalid transition: cancelled -> active" or "cannot be reactivated"
        assert "cancelled" in msg

    def test_cancelled_to_suspended_raises(self):
        """Cancelled → suspended is not in TRANSITIONS["cancelled"]."""
        tid = _provision("guard-c2s")
        transition_subscription_status(tid, "cancelled")
        with pytest.raises(ValueError) as exc_info:
            transition_subscription_status(tid, "suspended")
        assert "invalid transition" in str(exc_info.value).lower()

    def test_active_to_trial_raises(self):
        """Rolling back to trial from active is not allowed."""
        tid = _provision("guard-a2trial")
        transition_subscription_status(tid, "active")
        with pytest.raises(ValueError) as exc_info:
            transition_subscription_status(tid, "trial")
        assert "invalid transition" in str(exc_info.value).lower()

    def test_garbage_status_raises(self):
        """Unrecognised status raises ValueError about invalid subscription status."""
        tid = _provision("guard-garbage")
        with pytest.raises(ValueError) as exc_info:
            transition_subscription_status(tid, "banana")
        assert "invalid subscription status" in str(exc_info.value).lower()

    def test_empty_status_raises(self):
        tid = _provision("guard-empty")
        with pytest.raises(ValueError):
            transition_subscription_status(tid, "")


# ─── Category 3: Trial expiry logic ──────────────────────────────────────────

class TestTrialExpiry:
    def test_expired_trial_becomes_suspended_by_default(self):
        """When trial_ends_at is in the past, get_tenant_subscription returns suspended."""
        past = _utc_now() - timedelta(days=5)
        tid = _provision("expiry-suspended")
        # Force trial_ends_at to past
        ensure_tenant_subscription(
            tid,
            plan_code="free",
            status="trial",
            trial_ends_at=past.isoformat(),
        )
        sub = get_tenant_subscription(tid)
        assert sub is not None
        assert sub["status"] == "suspended", (
            f"Expected suspended after trial expiry, got {sub['status']}"
        )

    def test_expired_trial_auto_activates_when_env_enabled(self, monkeypatch):
        """BILLING_TRIAL_AUTO_ACTIVATE=true → expired trial becomes active."""
        monkeypatch.setenv("BILLING_TRIAL_AUTO_ACTIVATE", "true")
        past = _utc_now() - timedelta(days=1)
        tid = _provision("expiry-autoactivate")
        ensure_tenant_subscription(
            tid,
            plan_code="free",
            status="trial",
            trial_ends_at=past.isoformat(),
        )
        sub = get_tenant_subscription(tid)
        assert sub is not None
        assert sub["status"] == "active", (
            f"Expected active due to auto-activate, got {sub['status']}"
        )

    def test_missing_trial_end_becomes_suspended_failsafe(self):
        """trial_ends_at=None → fail-safe suspend to prevent infinite trial."""
        tid = _provision("expiry-failsafe")
        # Manually inject a subscription record with no trial_ends_at
        with billing_service._state_lock:
            billing_service._state.subscriptions[tid] = {
                "tenant_id": tid,
                "plan_id": 1,
                "plan_code": "free",
                "status": "trial",
                "started_at": _utc_now().isoformat(),
                "trial_ends_at": None,
                "current_period_start": _utc_now().isoformat(),
                "current_period_end": (_utc_now() + timedelta(days=30)).isoformat(),
                "next_plan_id": None,
                "next_plan_code": None,
                "updated_at": _utc_now().isoformat(),
            }
        sub = get_tenant_subscription(tid)
        assert sub is not None
        assert sub["status"] == "suspended", (
            f"Expected suspended (fail-safe for missing trial_ends_at), got {sub['status']}"
        )

    def test_active_trial_not_expired_remains_trial(self):
        """trial_ends_at in the future → status stays trial."""
        future = _utc_now() + timedelta(days=7)
        tid = _provision("expiry-notexpired")
        ensure_tenant_subscription(
            tid,
            plan_code="free",
            status="trial",
            trial_ends_at=future.isoformat(),
        )
        sub = get_tenant_subscription(tid)
        assert sub is not None
        assert sub["status"] == "trial"

    def test_monkeypatched_now_triggers_expiry(self, monkeypatch):
        """Monkeypatching _now() to future causes the service to see trial as expired."""
        future_trial_end = _utc_now() + timedelta(days=3)
        tid = _provision("expiry-monkeypatch")
        ensure_tenant_subscription(
            tid,
            plan_code="free",
            status="trial",
            trial_ends_at=future_trial_end.isoformat(),
        )
        # Advance time past trial end
        future_now = _utc_now() + timedelta(days=10)
        monkeypatch.setattr(billing_service, "_now", lambda: future_now)

        sub = get_tenant_subscription(tid)
        assert sub is not None
        assert sub["status"] == "suspended"


# ─── Category 4: PLAN_RANK upgrade / downgrade auto logic ────────────────────

class TestPlanChangeRank:
    def test_upgrade_auto_is_immediate(self):
        """free→enterprise with effective=auto: PLAN_RANK(enterprise=3)>PLAN_RANK(free=0) → immediate."""
        tid = _provision("rank-upgrade")
        result = change_subscription_plan(tid, "enterprise", effective="auto")
        assert result["effective"] == "immediate"
        assert result["new_plan"] == "enterprise"
        # Subscription is updated immediately
        sub = get_tenant_subscription(tid)
        assert sub["plan_code"] == "enterprise"
        assert sub.get("next_plan_code") is None

    def test_downgrade_auto_is_next_period(self):
        """enterprise→free with effective=auto: PLAN_RANK(free=0)<PLAN_RANK(enterprise=3) → next_period."""
        tid = _provision("rank-downgrade")
        # Start on enterprise
        ensure_tenant_subscription(tid, plan_code="enterprise", status="active")
        result = change_subscription_plan(tid, "free", effective="auto")
        assert result["effective"] == "next_period"
        assert result["new_plan"] == "free"
        # Current plan stays, downgrade is scheduled
        sub = get_tenant_subscription(tid)
        assert sub["plan_code"] == "enterprise"
        assert sub["next_plan_code"] == "free"

    def test_same_rank_upgrade_auto_is_immediate(self):
        """Same rank (free→free): effective=auto → immediate (>=)."""
        tid = _provision("rank-same")
        result = change_subscription_plan(tid, "free", effective="auto")
        assert result["effective"] == "immediate"

    def test_explicit_immediate_forces_immediate_for_downgrade(self):
        """explicit effective=immediate bypasses PLAN_RANK logic."""
        tid = _provision("rank-explicit-imm")
        ensure_tenant_subscription(tid, plan_code="enterprise", status="active")
        result = change_subscription_plan(tid, "free", effective="immediate")
        assert result["effective"] == "immediate"
        sub = get_tenant_subscription(tid)
        assert sub["plan_code"] == "free"

    def test_explicit_next_period_forces_next_period_for_upgrade(self):
        """explicit effective=next_period bypasses PLAN_RANK logic for upgrades."""
        tid = _provision("rank-explicit-np")
        result = change_subscription_plan(tid, "enterprise", effective="next_period")
        assert result["effective"] == "next_period"
        sub = get_tenant_subscription(tid)
        assert sub["plan_code"] == "free"
        assert sub["next_plan_code"] == "enterprise"

    def test_invalid_effective_raises(self):
        """effective='gobbledygook' raises ValueError."""
        tid = _provision("rank-invalid-eff")
        with pytest.raises(ValueError) as exc_info:
            change_subscription_plan(tid, "pro", effective="gobbledygook")
        assert "effective must be one of" in str(exc_info.value).lower()

    def test_nonexistent_plan_raises(self):
        """Target plan that doesn't exist raises ValueError."""
        tid = _provision("rank-no-plan")
        with pytest.raises(ValueError) as exc_info:
            change_subscription_plan(tid, "nonexistent_plan_xyz")
        assert "plan not found" in str(exc_info.value).lower()


# ─── Category 5: Period rollover ─────────────────────────────────────────────

class TestPeriodRollover:
    def test_period_rollover_applies_next_plan_at_boundary(self, monkeypatch):
        """When current_period_end is in the past, next_plan_code gets applied."""
        past_period_start = _utc_now() - timedelta(days=60)
        past_period_end = _utc_now() - timedelta(days=30)
        _utc_now() + timedelta(days=30)

        tid = _provision("rollover-plan")
        # Set subscription on pro plan with scheduled downgrade to basic
        ensure_tenant_subscription(
            tid,
            plan_code="pro",
            status="active",
            current_period_start=past_period_start.isoformat(),
            current_period_end=past_period_end.isoformat(),
            next_plan_code="basic",
        )
        sub = get_tenant_subscription(tid)
        assert sub is not None
        # After rollover, plan should be basic and next_plan_code cleared
        assert sub["plan_code"] == "basic", (
            f"Expected plan to roll over to basic, got {sub['plan_code']}"
        )
        assert sub.get("next_plan_code") is None

    def test_no_rollover_within_active_period(self):
        """If period_end is in the future, no rollover happens."""
        future_end = _utc_now() + timedelta(days=15)
        tid = _provision("rollover-no")
        ensure_tenant_subscription(
            tid,
            plan_code="pro",
            status="active",
            current_period_end=future_end.isoformat(),
            next_plan_code="free",
        )
        sub = get_tenant_subscription(tid)
        assert sub["plan_code"] == "pro"
        assert sub["next_plan_code"] == "free"

    def test_period_rollover_advances_period_dates(self, monkeypatch):
        """After rollover, current_period_start/end advance by billing period."""
        past_period_end = _utc_now() - timedelta(days=1)
        past_period_start = past_period_end - timedelta(days=30)
        tid = _provision("rollover-dates")
        ensure_tenant_subscription(
            tid,
            plan_code="free",
            status="active",
            current_period_start=past_period_start.isoformat(),
            current_period_end=past_period_end.isoformat(),
        )
        sub = get_tenant_subscription(tid)
        assert sub is not None
        # New period should start at old period_end
        new_start = billing_service._parse_dt(sub["current_period_start"])
        assert new_start is not None
        assert new_start >= past_period_end - timedelta(seconds=5)


# ─── Category 6: assert_billing_write_allowed ────────────────────────────────

class TestBillingWriteGuard:
    def test_trial_allows_write(self):
        tid = _provision("write-trial")
        # Should NOT raise
        assert_billing_write_allowed(tid, action="create_enrollment")

    def test_active_allows_write(self):
        tid = _provision("write-active")
        transition_subscription_status(tid, "active")
        assert_billing_write_allowed(tid, action="create_grade")

    def test_suspended_blocks_write(self):
        tid = _provision("write-suspended")
        transition_subscription_status(tid, "suspended")
        with pytest.raises(HTTPException) as exc_info:
            assert_billing_write_allowed(tid, action="enroll_student")
        exc = exc_info.value
        assert exc.status_code == 403
        assert "billing_required" in str(exc.detail).lower()
        assert "suspended" in str(exc.detail).lower()

    def test_cancelled_blocks_write(self):
        tid = _provision("write-cancelled")
        transition_subscription_status(tid, "cancelled")
        with pytest.raises(HTTPException) as exc_info:
            assert_billing_write_allowed(tid, action="create_course")
        exc = exc_info.value
        assert exc.status_code == 403
        assert "billing_required" in str(exc.detail).lower()

    def test_write_guard_error_message_includes_action_context(self):
        """The 403 detail must identify the status clearly for observability."""
        tid = _provision("write-detail")
        transition_subscription_status(tid, "suspended")
        with pytest.raises(HTTPException) as exc_info:
            assert_billing_write_allowed(tid, action="test_action_ctx")
        detail = str(exc_info.value.detail)
        assert "suspended" in detail


# ─── Category 7: assert_quota_with_increment ─────────────────────────────────

class TestQuotaEnforcement:
    def test_within_quota_passes(self):
        """Increment within limit returns within_limit=True."""
        tid = _provision("quota-within")
        result = assert_quota_with_increment(tid, "users", increment=1)
        assert result["within_limit"] is True

    def test_over_quota_raises_403(self):
        """Increment over hard limit raises HTTPException 403."""
        tid = _provision("quota-over")
        transition_subscription_status(tid, "active")

        # Set a hard limit of 3 grades_submitted for the free plan
        plan = get_plan_by_code("free")
        assert plan is not None, "free plan must exist"
        update_plan_quotas(int(plan["id"]), quotas={"grades_submitted": 3})

        # Record 3 grades already submitted (at the limit)
        from app.modules.usage.service import record_usage_event
        record_usage_event(tid, metric="grades_submitted", value=3)

        # Attempting to submit 1 more should exceed limit (3+1 > 3)
        with pytest.raises(HTTPException) as exc_info:
            assert_quota_with_increment(tid, "grades_submitted", increment=1)
        exc = exc_info.value
        assert exc.status_code == 403
        assert "billing_required" in str(exc.detail).lower()
        assert "quota exceeded" in str(exc.detail).lower()

    def test_quota_result_contains_projected_value(self):
        tid = _provision("quota-result")
        result = assert_quota_with_increment(tid, "users", increment=3)
        assert "projected_value" in result
        assert int(result["projected_value"]) >= 3


# ─── Category 8: get_tenant_billing_state ────────────────────────────────────

class TestBillingState:
    def test_trial_returns_read_write(self):
        tid = _provision("state-trial")
        state = get_tenant_billing_state(tid)
        assert state["billing_state"] == "read_write"
        assert state["subscription_status"] == "trial"

    def test_active_returns_read_write(self):
        tid = _provision("state-active")
        transition_subscription_status(tid, "active")
        state = get_tenant_billing_state(tid)
        assert state["billing_state"] == "read_write"

    def test_suspended_returns_read_only(self):
        tid = _provision("state-suspended")
        transition_subscription_status(tid, "suspended")
        state = get_tenant_billing_state(tid)
        assert state["billing_state"] == "read_only"
        assert state["subscription_status"] == "suspended"

    def test_cancelled_returns_read_only(self):
        tid = _provision("state-cancelled")
        transition_subscription_status(tid, "cancelled")
        state = get_tenant_billing_state(tid)
        assert state["billing_state"] == "read_only"

    def test_billing_state_contains_plan_and_usage(self):
        tid = _provision("state-full")
        state = get_tenant_billing_state(tid)
        assert "plan_code" in state
        assert "usage" in state
        assert "limits" in state
        assert "subscription" in state

    def test_nonexistent_tenant_raises_value_error(self):
        with pytest.raises(ValueError) as exc_info:
            get_tenant_billing_state(99999999)
        assert "not found" in str(exc_info.value).lower()


# ─── Category 9: Multi-tenant state isolation ────────────────────────────────

class TestMultiTenantIsolation:
    def test_two_tenants_independent_states(self):
        """Changes to tenant A's subscription MUST NOT affect tenant B."""
        tid_a = _provision("isolation-a", plan="pro")
        tid_b = _provision("isolation-b", plan="free")

        # Put A through a full lifecycle
        transition_subscription_status(tid_a, "active")
        transition_subscription_status(tid_a, "suspended")

        # B should still be trial
        sub_b = get_tenant_subscription(tid_b)
        assert sub_b is not None
        assert sub_b["status"] == "trial"
        assert sub_b["plan_code"] == "free"

    def test_two_tenants_independent_plans(self):
        """Changing A's plan must not cascade to B."""
        tid_a = _provision("isolation-plan-a")
        tid_b = _provision("isolation-plan-b")

        change_subscription_plan(tid_a, "enterprise", effective="immediate")

        sub_b = get_tenant_subscription(tid_b)
        assert sub_b is not None
        assert sub_b["plan_code"] == "free", (
            f"Tenant B plan contaminated: expected free, got {sub_b['plan_code']}"
        )

    def test_billing_state_read_only_for_a_does_not_block_b(self):
        """If A is suspended, B (trial/active) must still be writable."""
        tid_a = _provision("isolation-write-a")
        tid_b = _provision("isolation-write-b")

        transition_subscription_status(tid_a, "suspended")

        # B should still pass write guard
        assert_billing_write_allowed(tid_b, action="test_isolation")

    def test_quota_counters_independent_per_tenant(self):
        """Usage counters for tenant A must not affect tenant B's quota check."""
        tid_a = _provision("isolation-quota-a")
        tid_b = _provision("isolation-quota-b")

        plan = get_plan_by_code("free")
        assert plan is not None
        # Set limit of 5 grades_submitted per tenant
        update_plan_quotas(int(plan["id"]), quotas={"grades_submitted": 5})

        # Record 4 grades for A (near limit)
        from app.modules.usage.service import record_usage_event
        record_usage_event(tid_a, metric="grades_submitted", value=4)

        # B should still be well within limit (0 usage)
        result_b = assert_quota_with_increment(tid_b, "grades_submitted", increment=1)
        assert result_b["within_limit"] is True
