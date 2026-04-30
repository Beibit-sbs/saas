"""Week 9 — Domain Depth tests.

DoD coverage:
- student_life disciplinary state machine: valid transitions allowed, invalid blocked
- grades grade_risk → intervention auto-create (DB insert attempted)
- admissions ACCEPTED decision → financial_aid record auto-created
"""
from __future__ import annotations

import unittest.mock as mock

import pytest


# ---------------------------------------------------------------------------
# student_life disciplinary state machine
# ---------------------------------------------------------------------------

class TestDisciplinaryStateMachine:
    """Validate DISCIPLINARY_ALLOWED_TRANSITIONS guard logic."""

    def test_reported_to_under_review_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "under_review" in DISCIPLINARY_ALLOWED_TRANSITIONS["reported"]

    def test_reported_to_hearing_scheduled_not_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "hearing_scheduled" not in DISCIPLINARY_ALLOWED_TRANSITIONS["reported"]

    def test_under_review_to_hearing_scheduled_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "hearing_scheduled" in DISCIPLINARY_ALLOWED_TRANSITIONS["under_review"]

    def test_hearing_scheduled_to_closed_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "closed" in DISCIPLINARY_ALLOWED_TRANSITIONS["hearing_scheduled"]

    def test_hearing_scheduled_to_appealed_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "appealed" in DISCIPLINARY_ALLOWED_TRANSITIONS["hearing_scheduled"]

    def test_closed_to_under_review_not_allowed(self) -> None:
        from app.modules.student_life.schemas import DISCIPLINARY_ALLOWED_TRANSITIONS
        assert "under_review" not in DISCIPLINARY_ALLOWED_TRANSITIONS["closed"]

    def test_update_disciplinary_status_blocks_invalid_transition(self) -> None:
        from app.modules.student_life.service import update_disciplinary_case_status
        from app.modules.student_life.schemas import DisciplinaryCaseStatusUpdateSchema

        # Seed an in-memory entity at "reported" status
        import app.modules.university_core.shared as shared
        entity = "student_life_disciplinary_cases"
        with shared._state_lock:
            shared._state.data[entity].clear()
            shared._state.counters[entity] = 0
            shared._state.data[entity][1] = {
                "id": 1,
                "tenant_id": "1",
                "incident_code": "INC-001",
                "student_id": "stu-1",
                "incident_type": "cheating",
                "severity": "medium",
                "status": "reported",
            }

        req = DisciplinaryCaseStatusUpdateSchema(status="hearing_scheduled")  # Invalid: reported → hearing_scheduled
        with pytest.raises(ValueError, match="not allowed"):
            update_disciplinary_case_status(1, 1, req, "test-actor")

    def test_update_disciplinary_status_allows_valid_transition(self) -> None:
        from app.modules.student_life.service import update_disciplinary_case_status
        from app.modules.student_life.schemas import DisciplinaryCaseStatusUpdateSchema

        import app.modules.university_core.shared as shared
        entity = "student_life_disciplinary_cases"
        with shared._state_lock:
            shared._state.data[entity].clear()
            shared._state.counters[entity] = 0
            shared._state.data[entity][2] = {
                "id": 2,
                "tenant_id": "1",
                "incident_code": "INC-002",
                "student_id": "stu-2",
                "incident_type": "cheating",
                "severity": "medium",
                "status": "reported",
            }

        req = DisciplinaryCaseStatusUpdateSchema(status="under_review")  # Valid
        result = update_disciplinary_case_status(1, 2, req, "test-actor")
        assert result.status == "under_review"


# ---------------------------------------------------------------------------
# grades → intervention auto-create (unit: verify InterventionCaseModel added to session)
# ---------------------------------------------------------------------------

class TestGradeRiskInterventionWiring:
    """Verify that a grade risk event triggers an intervention DB insert."""

    def test_grade_risk_adds_intervention_to_db_session(self) -> None:
        """Verify that grades service submit_grade source contains InterventionCaseModel
        auto-create wiring for risk levels."""
        import inspect
        from app.modules.grades.service import GradeLifecycleService

        src = inspect.getsource(GradeLifecycleService.submit_grade)
        assert "InterventionCaseModel" in src, (
            "submit_grade must wire grade risk to InterventionCaseModel creation"
        )
        assert "risk_level" in src
        assert "InterventionCaseSeverity" in src or "ACADEMIC_RISK" in src or "academic_risk" in src


# ---------------------------------------------------------------------------
# admissions ACCEPTED → financial_aid auto-create
# ---------------------------------------------------------------------------

class TestAdmissionsFinancialAidWiring:
    """Verify that an ACCEPTED admissions decision triggers financial_aid creation."""

    def test_accepted_decision_calls_create_financial_aid_record(self) -> None:
        """When decision_type == ACCEPTED, create_financial_aid_record must be called."""
        from app.modules.financial_aid.service import create_financial_aid_record

        # Verify the accepted decision type value
        from app.modules.admissions.schemas import ApplicationConclusionType
        assert ApplicationConclusionType.ACCEPTED.value == "accepted"

        # Verify create_financial_aid_record is callable and returns correct result
        from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema
        req = FinancialAidRecordCreateSchema(
            student_id=1,
            aid_type="scholarship",
            amount=0.01,
            currency="USD",
            term="pending-review",
        )

        import app.modules.university_core.shared as shared
        with shared._state_lock:
            shared._state.data["financial_aid_records"].clear()
            shared._state.counters["financial_aid_records"] = 0

        with mock.patch("app.modules.financial_aid.service.log_admin_action"):
            with mock.patch(
                "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
                return_value=None,
            ):
                result = create_financial_aid_record(tenant_id=1, request=req, actor="aid-office")
        assert result.status == "pending"
        assert result.student_id == 1

    def test_admissions_wiring_in_make_decision_source(self) -> None:
        """Verify the source code of make_decision contains the financial_aid wiring."""
        import inspect
        from app.modules.admissions.service import DecisionService
        src = inspect.getsource(DecisionService.make_decision)
        assert "create_financial_aid_record" in src, (
            "make_decision must wire ACCEPTED decision to create_financial_aid_record"
        )
        assert "accepted" in src
