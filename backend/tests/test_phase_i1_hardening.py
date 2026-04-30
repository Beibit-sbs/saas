"""Phase I1 hardening tests.

Covers:
  I1.1 — thesis.status_changed canonical brain signal format
  I1.2 — advising session outcome signal emission
  I1.3 — students risk-context API endpoint
"""

from __future__ import annotations

from unittest.mock import patch


from tests.conftest import ADMIN_HEADERS, client


def _seed_advising_prereqs(student_id: int, advisor_id: str, tenant_id: int = 1) -> None:
    from app.modules.university_core.shared import _state, _state_lock

    with _state_lock:
        _state.data.setdefault("faculty", {})
        _state.counters.setdefault("faculty", 0)
        _state.counters["faculty"] += 1
        fid = _state.counters["faculty"]
        _state.data["faculty"][fid] = {
            "id": fid,
            "faculty_id": advisor_id,
            "first_name": "Test",
            "last_name": "Advisor",
            "department": "CS",
            "email": f"{advisor_id.lower()}@example.edu",
            "status": "active",
            "tenant_id": str(tenant_id),
        }

        _state.data.setdefault("enrollments", {})
        _state.counters.setdefault("enrollments", 0)
        _state.counters["enrollments"] += 1
        eid = _state.counters["enrollments"]
        _state.data["enrollments"][eid] = {
            "id": eid,
            "student_id": student_id,
            "course_id": 1,
            "semester": "Fall 2025",
            "status": "active",
            "tenant_id": str(tenant_id),
        }

# ---------------------------------------------------------------------------
# I1.1 — Thesis canonical signal format
# ---------------------------------------------------------------------------


def test_thesis_emit_canonical_signal_fields() -> None:
    """thesis.status_changed payload must include canonical brain signal fields."""
    from app.modules.thesis.service import _emit_domain_event

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    # EventPublisher is imported locally inside _emit_domain_event, so patch the source module.
    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_domain_event(
            tenant_id=42,
            thesis_id=7,
            student_id=101,
            advisor_faculty_id="FAC-X",
            from_status="under_review",
            to_status="rejected",
            days_since_last_milestone=75,
        )

    assert len(published) == 1
    payload = published[0]["payload_json"]

    # Canonical brain signal fields
    assert payload["source_entity_type"] == "thesis"
    assert payload["source_entity_id"] == "7"
    assert payload["advisor_id"] == "FAC-X"
    assert payload["faculty_id"] == "FAC-X"
    assert payload["days_since_last_milestone"] == 75
    assert payload["student_id"] == "101"
    assert payload["thesis_id"] == "7"

    # Status transition fields preserved for academic_chain_handler
    assert payload["from_status"] == "under_review"
    assert payload["to_status"] == "rejected"


def test_thesis_emit_default_days_since_last_milestone() -> None:
    """When no last_milestone_at recorded, days_since_last_milestone defaults to 0."""
    from app.modules.thesis.service import _emit_domain_event

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_domain_event(
            tenant_id=1,
            thesis_id=1,
            student_id=1,
            advisor_faculty_id="",
            from_status="draft",
            to_status="under_review",
        )

    assert published[0]["payload_json"]["days_since_last_milestone"] == 0


# ---------------------------------------------------------------------------
# I1.2 — Advising brain signal + outcome feedback
# ---------------------------------------------------------------------------


def test_advising_session_complete_emits_outcome_signal() -> None:
    """Completing an advising session must emit advising.session.outcome.recorded."""
    from app.modules.advising.service import _emit_outcome_signal

    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    # EventPublisher is imported locally inside _emit_outcome_signal.
    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _emit_outcome_signal(
            tenant_id=1,
            session_id=55,
            student_id=101,
            advisor_id="FAC-A",
            session_type="academic",
            outcome_status="completed",
            outcome="Graduation plan confirmed",
        )

    assert len(published) == 1
    assert published[0]["event_type"] == "advising.session.outcome.recorded"
    payload = published[0]["payload_json"]
    assert payload["source_entity_type"] == "advising_session"
    assert payload["source_entity_id"] == "55"
    assert payload["outcome_status"] == "completed"
    assert payload["student_id"] == "101"


def test_advising_update_to_completed_emits_signal_via_api() -> None:
    """PATCH advising session to completed triggers outcome signal emission."""
    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _seed_advising_prereqs(student_id=201, advisor_id="FAC-B")
        # Create session
        create_resp = client.post(
            "/api/admin/advising",
            headers=ADMIN_HEADERS,
            json={
                "student_id": 201,
                "advisor_id": "FAC-B",
                "session_type": "academic",
                "scheduled_at": "2026-06-01T10:00",
                "notes": "Thesis planning",
            },
        )
        assert create_resp.status_code == 200
        session_id = create_resp.json()["item"]["id"]

        # Complete the session
        patch_resp = client.patch(
            f"/api/admin/advising/{session_id}/status",
            headers=ADMIN_HEADERS,
            json={"status": "completed", "outcome": "All milestones reviewed"},
        )
        assert patch_resp.status_code == 200

    # Outcome signal should have been emitted
    outcome_events = [e for e in published if e.get("event_type") == "advising.session.outcome.recorded"]
    assert len(outcome_events) >= 1
    assert outcome_events[0]["payload_json"]["outcome_status"] == "completed"


def test_advising_update_to_no_show_emits_signal() -> None:
    """PATCH advising session to no_show also triggers outcome signal."""
    published: list[dict] = []

    class _FakePublisher:
        def publish_event(self, **kwargs: object) -> dict:
            published.append(dict(kwargs))
            return {}

    with patch("app.platform.events.publisher.EventPublisher", return_value=_FakePublisher()):
        _seed_advising_prereqs(student_id=202, advisor_id="FAC-C")
        create_resp = client.post(
            "/api/admin/advising",
            headers=ADMIN_HEADERS,
            json={
                "student_id": 202,
                "advisor_id": "FAC-C",
                "session_type": "academic",
                "scheduled_at": "2026-06-02T10:00",
                "notes": "Thesis check",
            },
        )
        assert create_resp.status_code == 200
        session_id = create_resp.json()["item"]["id"]

        patch_resp = client.patch(
            f"/api/admin/advising/{session_id}/status",
            headers=ADMIN_HEADERS,
            json={"status": "no_show", "outcome": "Student absent"},
        )
        assert patch_resp.status_code == 200

    outcome_events = [e for e in published if e.get("event_type") == "advising.session.outcome.recorded"]
    assert len(outcome_events) >= 1
    assert outcome_events[0]["payload_json"]["outcome_status"] == "no_show"


# ---------------------------------------------------------------------------
# I1.3 — Students risk-context API
# ---------------------------------------------------------------------------


def test_student_risk_context_returns_200() -> None:
    """GET /api/admin/students/{id}/risk-context returns 200 with expected schema."""
    resp = client.get("/api/admin/students/1/risk-context", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "student_id" in body
    assert "tenant_id" in body
    assert "open_interventions" in body
    assert "recent_advising_sessions" in body
    assert "risk_flags" in body
    assert isinstance(body["risk_flags"], list)


def test_student_risk_context_requires_auth() -> None:
    resp = client.get("/api/admin/students/1/risk-context")
    assert resp.status_code in (401, 403)


def test_student_risk_context_service_aggregates_data() -> None:
    """get_student_risk_context correctly counts advising sessions and risk flags."""
    from app.modules.students.service import get_student_risk_context
    from app.modules.university_core.tenant_entity_api import create_entity_for_tenant

    tenant_id = 9999

    # Seed advising sessions for student 501 (advising_sessions IS in ENTITY_CONFIGS)
    create_entity_for_tenant(
        "advising_sessions",
        {
            "student_id": 501,
            "advisor_id": "FAC-D",
            "session_type": "academic",
            "status": "completed",
            "outcome": "thesis_reviewed",
            "scheduled_at": "2026-01-01",
            "notes": "Session notes",
        },
        tenant_id,
    )
    create_entity_for_tenant(
        "advising_sessions",
        {
            "student_id": 501,
            "advisor_id": "FAC-D",
            "session_type": "academic",
            "status": "no_show",
            "outcome": "pending",
            "scheduled_at": "2026-02-01",
            "notes": "No-show session",
        },
        tenant_id,
    )

    ctx = get_student_risk_context(tenant_id, 501)
    assert ctx["student_id"] == "501"
    assert ctx["recent_advising_sessions"] == 2
    assert ctx["last_advising_outcome"] == "thesis_reviewed"
    # no_show in sessions → risk flag
    assert "advising_no_show" in ctx["risk_flags"]
    # open_interventions defaults to 0 (intervention_cases not in entity store)
    assert ctx["open_interventions"] == 0
    assert isinstance(ctx["risk_flags"], list)
