"""
Phase XXXIII.4 — Admissions Transition Guard Matrix tests.

10 required test cases:
 1. valid NEW→RECEIVED succeeds
 2. valid transition emits admissions.application.submitted
 3. invalid NEW→CONCLUDED is blocked
 4. invalid RECEIVED→CONCLUDED is blocked
 5. rejected/concluded terminal states cannot transition back
 6. DECISION_PENDING→CONCLUDED succeeds only through finalization flow
 7. blocked transition emits no event
 8. blocked transition does not persist state change
 9. tenant mismatch remains blocked
10. valid transition publishes event only after successful persistence
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.modules.admissions.schemas import ApplicationStage
from app.modules.admissions.service import (
    ADMISSIONS_ALLOWED_STAGE_TRANSITIONS,
    _assert_stage_transition_allowed,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal ApplicationModel mock at a given stage
# ---------------------------------------------------------------------------
def _app_mock(stage: ApplicationStage, tenant_id: int = 1, app_id: int = 42) -> MagicMock:
    app = MagicMock()
    app.id = app_id
    app.tenant_id = tenant_id
    app.stage = stage.value
    app.version = 1
    app.metadata_json = {"workflow_instance_id": 99}
    app.conclusion_type = None
    app.decision_at = None
    return app


# ===========================================================================
# 1. valid NEW→RECEIVED succeeds
# ===========================================================================
def test_guard_allows_new_to_received():
    """Guard must not raise for the valid NEW→RECEIVED transition."""
    _assert_stage_transition_allowed(ApplicationStage.NEW, ApplicationStage.RECEIVED)


# ===========================================================================
# 2. valid transition (NEW→RECEIVED) emits admissions.application.submitted
# ===========================================================================
def test_submit_application_emits_event_on_valid_transition():
    """
    ApplicationService.submit_application emits 'admissions.application.submitted'
    when NEW→RECEIVED succeeds.
    """
    from app.modules.admissions.service import ApplicationService

    mock_db = MagicMock()

    application = _app_mock(ApplicationStage.NEW)
    application.applicant_id = 10
    application.program_id = 5

    # DB execute returns the application on first call, None on workflow id check
    mock_db.execute.return_value.scalar_one_or_none.return_value = application

    fake_schema = MagicMock()

    with (
        patch(
            "app.modules.admissions.service.ApplicationService._start_admissions_workflow",
        ) as mock_wf,
        patch("app.modules.admissions.service.EventPublisher") as mock_publisher_cls,
        patch("app.modules.admissions.service.log_admin_action"),
        patch(
            "app.modules.admissions.service.ApplicationReadSchema.model_validate",
            return_value=fake_schema,
        ),
    ):
        mock_wf_instance = MagicMock()
        mock_wf_instance.id = 99
        mock_wf.return_value = mock_wf_instance

        publisher_instance = MagicMock()
        mock_publisher_cls.return_value = publisher_instance

        import asyncio

        svc = ApplicationService(mock_db)
        asyncio.get_event_loop().run_until_complete(
            svc.submit_application(
                tenant_id=1,
                application_id=42,
                actor="admin@example.com",
                expected_version=1,
            )
        )

    publisher_instance.publish_event.assert_called_once()
    call_kwargs = publisher_instance.publish_event.call_args
    assert call_kwargs.kwargs["event_type"] == "admissions.application.submitted"


# ===========================================================================
# 3. invalid NEW→CONCLUDED is blocked
# ===========================================================================
def test_guard_blocks_new_to_concluded():
    """NEW stage must not be able to skip directly to CONCLUDED."""
    with pytest.raises(ValueError, match="Stage transition blocked"):
        _assert_stage_transition_allowed(ApplicationStage.NEW, ApplicationStage.CONCLUDED)


# ===========================================================================
# 4. invalid RECEIVED→CONCLUDED is blocked
# ===========================================================================
def test_guard_blocks_received_to_concluded():
    """RECEIVED stage must not jump directly to CONCLUDED."""
    with pytest.raises(ValueError, match="Stage transition blocked"):
        _assert_stage_transition_allowed(ApplicationStage.RECEIVED, ApplicationStage.CONCLUDED)


# ===========================================================================
# 5. rejected/concluded terminal states cannot transition back
# ===========================================================================
def test_concluded_is_terminal_no_outbound_transitions():
    """CONCLUDED must have no allowed outbound transitions."""
    allowed = ADMISSIONS_ALLOWED_STAGE_TRANSITIONS[ApplicationStage.CONCLUDED]
    assert allowed == frozenset(), (
        "CONCLUDED must be a terminal state with no allowed outbound transitions"
    )


def test_guard_blocks_concluded_to_all_other_stages():
    """Every stage transition OUT of CONCLUDED must be blocked."""
    for target in ApplicationStage:
        with pytest.raises(ValueError, match="Stage transition blocked"):
            _assert_stage_transition_allowed(ApplicationStage.CONCLUDED, target)


# ===========================================================================
# 6. DECISION_PENDING→CONCLUDED succeeds only through finalization flow
# ===========================================================================
def test_guard_allows_decision_pending_to_concluded():
    """DECISION_PENDING is the only valid predecessor for CONCLUDED."""
    _assert_stage_transition_allowed(ApplicationStage.DECISION_PENDING, ApplicationStage.CONCLUDED)


def test_guard_blocks_under_review_to_concluded():
    """UNDER_REVIEW must not skip to CONCLUDED directly."""
    with pytest.raises(ValueError, match="Stage transition blocked"):
        _assert_stage_transition_allowed(ApplicationStage.UNDER_REVIEW, ApplicationStage.CONCLUDED)


# ===========================================================================
# 7. blocked transition emits no event
# ===========================================================================
def test_blocked_transition_emits_no_event():
    """
    When StageTransitionService.transition_stage is called with a blocked
    transition (e.g. RECEIVED→CONCLUDED), no event should be published.
    """
    from app.modules.admissions.service import StageTransitionService
    from app.modules.admissions.schemas import StageTransitionRequestSchema, StageTransitionAction

    mock_db = MagicMock()
    application = _app_mock(ApplicationStage.RECEIVED)
    mock_db.execute.return_value.scalar_one_or_none.return_value = application

    with patch("app.modules.admissions.service.EventPublisher") as mock_publisher_cls:
        publisher_instance = MagicMock()
        mock_publisher_cls.return_value = publisher_instance

        svc = StageTransitionService(mock_db)
        request = StageTransitionRequestSchema(
            to_stage=ApplicationStage.CONCLUDED,
            reason="attempt skip",
            action_type=StageTransitionAction.MANUAL,
        )

        import asyncio

        with pytest.raises(ValueError, match="Stage transition blocked"):
            asyncio.get_event_loop().run_until_complete(
                svc.transition_stage(
                    tenant_id=1,
                    application_id=42,
                    request=request,
                    actor_id="admin@example.com",
                )
            )

    publisher_instance.publish_event.assert_not_called()


# ===========================================================================
# 8. blocked transition does not persist state change
# ===========================================================================
def test_blocked_transition_does_not_persist():
    """
    When a blocked transition is attempted, db.flush and db.add must
    not be called — no state is persisted.
    """
    from app.modules.admissions.service import StageTransitionService
    from app.modules.admissions.schemas import StageTransitionRequestSchema, StageTransitionAction

    mock_db = MagicMock()
    application = _app_mock(ApplicationStage.NEW)
    mock_db.execute.return_value.scalar_one_or_none.return_value = application

    svc = StageTransitionService(mock_db)
    request = StageTransitionRequestSchema(
        to_stage=ApplicationStage.CONCLUDED,
        reason="skip attempt",
        action_type=StageTransitionAction.MANUAL,
    )

    import asyncio

    with pytest.raises(ValueError, match="Stage transition blocked"):
        asyncio.get_event_loop().run_until_complete(
            svc.transition_stage(
                tenant_id=1,
                application_id=42,
                request=request,
                actor_id="admin@example.com",
            )
        )

    mock_db.flush.assert_not_called()
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


# ===========================================================================
# 9. tenant mismatch remains blocked
# ===========================================================================
def test_transition_blocked_on_tenant_mismatch():
    """
    When the application is not found for the given tenant, a ValueError
    is raised — tenant isolation is enforced regardless of the transition.
    """
    from app.modules.admissions.service import StageTransitionService
    from app.modules.admissions.schemas import StageTransitionRequestSchema, StageTransitionAction

    mock_db = MagicMock()
    # Simulate application not found (belongs to a different tenant)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    svc = StageTransitionService(mock_db)
    request = StageTransitionRequestSchema(
        to_stage=ApplicationStage.UNDER_REVIEW,
        reason="review",
        action_type=StageTransitionAction.MANUAL,
    )

    import asyncio

    with pytest.raises(ValueError, match="not found"):
        asyncio.get_event_loop().run_until_complete(
            svc.transition_stage(
                tenant_id=999,  # wrong tenant
                application_id=42,
                request=request,
                actor_id="admin@example.com",
            )
        )


# ===========================================================================
# 10. valid transition publishes event only after successful persistence
# ===========================================================================
def test_valid_transition_publishes_event_after_persistence():
    """
    For a valid RECEIVED→UNDER_REVIEW transition, the event is published
    only after db.flush() is called (i.e. after persistence attempt).
    """
    from app.modules.admissions.service import StageTransitionService
    from app.modules.admissions.schemas import StageTransitionRequestSchema, StageTransitionAction

    call_order: list[str] = []
    mock_db = MagicMock()

    application = _app_mock(ApplicationStage.RECEIVED)
    history = MagicMock()
    history.id = 7
    history.created_at = datetime.now(UTC)

    mock_db.execute.return_value.scalar_one_or_none.return_value = application

    original_flush = mock_db.flush

    def record_flush():
        call_order.append("flush")

    mock_db.flush.side_effect = record_flush

    with (
        patch("app.modules.admissions.service.EventPublisher") as mock_publisher_cls,
        patch("app.modules.admissions.service.log_admin_action"),
        patch("app.modules.admissions.service.ApplicationStageHistoryModel", return_value=history),
    ):
        publisher_instance = MagicMock()

        def record_publish(**kwargs):
            call_order.append("publish")

        publisher_instance.publish_event.side_effect = record_publish
        mock_publisher_cls.return_value = publisher_instance

        svc = StageTransitionService(mock_db)
        request = StageTransitionRequestSchema(
            to_stage=ApplicationStage.UNDER_REVIEW,
            reason="start review",
            action_type=StageTransitionAction.MANUAL,
        )

        import asyncio

        asyncio.get_event_loop().run_until_complete(
            svc.transition_stage(
                tenant_id=1,
                application_id=42,
                request=request,
                actor_id="admin@example.com",
            )
        )

    assert "flush" in call_order, "db.flush must be called"
    assert "publish" in call_order, "publish_event must be called"
    flush_idx = call_order.index("flush")
    publish_idx = call_order.index("publish")
    assert flush_idx < publish_idx, (
        f"Event must be published after persistence (flush at {flush_idx}, publish at {publish_idx})"
    )
