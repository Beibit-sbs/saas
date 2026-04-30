"""W156 — faculty_copilot: Router _svc Hardening (Faculty Active Contract Guard).

Guard: W129 — faculty copilot access blocked unless faculty has active employment contract (fail-closed).
"""
from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

import app.modules.faculty_copilot.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty_copilot.schemas import (
    FacultyQnARequestSchema,
    LessonPlanRequestSchema,
    MaterialPackRequestSchema,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = 42
FACULTY_ID = "fac-001"


def _active_contract(faculty_id: str = FACULTY_ID) -> dict:
    return {"faculty_id": faculty_id, "status": "active"}


def _make_lesson_plan_payload(faculty_id: str = FACULTY_ID) -> LessonPlanRequestSchema:
    return LessonPlanRequestSchema(
        faculty_id=faculty_id,
        course_title="Advanced Algebra",
        topic="Linear Transformations",
        duration_minutes=60,
    )


def _make_material_payload(faculty_id: str = FACULTY_ID) -> MaterialPackRequestSchema:
    return MaterialPackRequestSchema(
        faculty_id=faculty_id,
        course_title="Advanced Algebra",
        topic="Linear Transformations",
        material_type="slides",
    )


def _make_qna_payload(faculty_id: str = FACULTY_ID) -> FacultyQnARequestSchema:
    return FacultyQnARequestSchema(
        faculty_id=faculty_id,
        question="How do I explain eigenvalues intuitively?",
    )


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_active_contract_statuses_is_frozenset(self):
        assert isinstance(svc._FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES, frozenset)

    def test_active_contract_statuses_contains_active(self):
        assert "active" in svc._FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_check_function_exists(self):
        assert callable(svc._check_faculty_has_active_contract_for_copilot)

    def test_generate_lesson_plan_exists(self):
        assert callable(svc.generate_lesson_plan)

    def test_generate_material_pack_exists(self):
        assert callable(svc.generate_material_pack)

    def test_answer_faculty_question_exists(self):
        assert callable(svc.answer_faculty_question)


# ---------------------------------------------------------------------------
# 2. Guard — allow paths
# ---------------------------------------------------------------------------

class TestGuardAllowPaths:
    def test_active_contract_passes(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            # Should not raise
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_multiple_contracts_one_active_passes(self):
        contracts = [
            {"faculty_id": FACULTY_ID, "status": "terminated"},
            {"faculty_id": FACULTY_ID, "status": "active"},
        ]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_faculty_id_whitespace_trimmed(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract("fac-001")]
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id="  fac-001  "
            )

    def test_status_case_insensitive(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "ACTIVE"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_alt_key_employee_id_passes(self):
        contracts = [{"employee_id": FACULTY_ID, "status": "active"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_alt_key_contract_status_passes(self):
        contracts = [{"faculty_id": FACULTY_ID, "contract_status": "active"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )


# ---------------------------------------------------------------------------
# 3. Guard — block paths
# ---------------------------------------------------------------------------

class TestGuardBlockPaths:
    def test_no_contracts_raises(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with pytest.raises(DomainValidationError, match="no faculty contract records found"):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_terminated_contract_raises(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "terminated"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError, match="no active contract"):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_resigned_contract_raises(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "resigned"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError, match="no active contract"):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_expired_contract_raises(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "expired"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_wrong_faculty_id_raises(self):
        contracts = [{"faculty_id": "other-faculty", "status": "active"}]
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError, match="no faculty contract records found"):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_error_message_contains_faculty_id(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )
            assert FACULTY_ID in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------

class TestFailClosed:
    def test_runtime_error_raises_domain_validation(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = RuntimeError("db down")
            with pytest.raises(DomainValidationError, match="lookup failed"):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_connection_error_raises_domain_validation(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = ConnectionError("timeout")
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_cause_preserved_on_lookup_failure(self):
        original = RuntimeError("original error")
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = original
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )
            assert exc_info.value.__cause__ is original

    def test_os_error_raises_domain_validation(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = OSError("io error")
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )


# ---------------------------------------------------------------------------
# 5. Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_guard_passes_correct_tenant_id(self):
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            svc._check_faculty_has_active_contract_for_copilot(
                tenant_id=99, faculty_id=FACULTY_ID
            )
            mock_list.assert_called_once_with("faculty_contracts", 99)

    def test_other_tenant_contracts_dont_satisfy_guard(self):
        # Guard for tenant 1 should only look at tenant 1's contracts
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            # Returns empty for tenant 1 (contracts belong to tenant 2)
            mock_list.return_value = []
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_copilot(
                    tenant_id=1, faculty_id=FACULTY_ID
                )
            mock_list.assert_called_once_with("faculty_contracts", 1)


# ---------------------------------------------------------------------------
# 6. Guard fires first in each service function
# ---------------------------------------------------------------------------

class TestGuardFiresFirst:
    def test_generate_lesson_plan_calls_guard_before_ai(self):
        payload = _make_lesson_plan_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []  # guard will block
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                with pytest.raises(DomainValidationError):
                    svc.generate_lesson_plan(
                        tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                    )
                mock_ai.answer_question.assert_not_called()

    def test_generate_material_pack_calls_guard_before_ai(self):
        payload = _make_material_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                with pytest.raises(DomainValidationError):
                    svc.generate_material_pack(
                        tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                    )
                mock_ai.answer_question.assert_not_called()

    def test_answer_faculty_question_calls_guard_before_ai(self):
        payload = _make_qna_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                with pytest.raises(DomainValidationError):
                    svc.answer_faculty_question(
                        tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                    )
                mock_ai.answer_question.assert_not_called()

    def test_generate_lesson_plan_proceeds_when_guard_passes(self):
        payload = _make_lesson_plan_payload()
        fake_answer = {"answer": "Here is your lesson plan", "sources": []}
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = fake_answer
                result = svc.generate_lesson_plan(
                    tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                )
                assert result == fake_answer
                mock_ai.answer_question.assert_called_once()

    def test_generate_material_pack_proceeds_when_guard_passes(self):
        payload = _make_material_payload()
        fake_answer = {"answer": "Here are your slides", "sources": []}
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = fake_answer
                result = svc.generate_material_pack(
                    tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                )
                assert result == fake_answer

    def test_answer_faculty_question_proceeds_when_guard_passes(self):
        payload = _make_qna_payload()
        fake_answer = {"answer": "Eigenvalues represent...", "sources": []}
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = fake_answer
                result = svc.answer_faculty_question(
                    tenant_id=TENANT_ID, actor_id="actor-1", payload=payload
                )
                assert result == fake_answer


# ---------------------------------------------------------------------------
# 7. AI service context shape
# ---------------------------------------------------------------------------

class TestAIContextShape:
    def test_lesson_plan_context_includes_faculty_id(self):
        payload = _make_lesson_plan_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = {"answer": "ok", "sources": []}
                svc.generate_lesson_plan(tenant_id=TENANT_ID, actor_id="actor-1", payload=payload)
                call_kwargs = mock_ai.answer_question.call_args.kwargs
                assert call_kwargs["context"]["faculty_id"] == FACULTY_ID
                assert call_kwargs["context"]["mode"] == "lesson_plan"

    def test_material_pack_context_includes_material_type(self):
        payload = _make_material_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = {"answer": "ok", "sources": []}
                svc.generate_material_pack(tenant_id=TENANT_ID, actor_id="actor-1", payload=payload)
                call_kwargs = mock_ai.answer_question.call_args.kwargs
                assert call_kwargs["context"]["material_type"] == "slides"
                assert call_kwargs["context"]["mode"] == "materials"

    def test_qna_context_includes_mode(self):
        payload = _make_qna_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = {"answer": "ok", "sources": []}
                svc.answer_faculty_question(tenant_id=TENANT_ID, actor_id="actor-1", payload=payload)
                call_kwargs = mock_ai.answer_question.call_args.kwargs
                assert call_kwargs["context"]["mode"] == "faculty_qna"

    def test_ai_receives_correct_tenant_id(self):
        payload = _make_lesson_plan_payload()
        with patch("app.modules.faculty_copilot.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            with patch("app.modules.faculty_copilot.service.ai_service") as mock_ai:
                mock_ai.answer_question.return_value = {"answer": "ok", "sources": []}
                svc.generate_lesson_plan(tenant_id=77, actor_id="actor-1", payload=payload)
                call_kwargs = mock_ai.answer_question.call_args.kwargs
                assert call_kwargs["tenant_id"] == 77


# ---------------------------------------------------------------------------
# 8. Router structure
# ---------------------------------------------------------------------------

class TestRouterStructure:
    def _read_router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/faculty_copilot/router.py").read_text()

    def test_router_imports_svc_module(self):
        source = self._read_router_source()
        assert "import app.modules.faculty_copilot.service as _svc" in source

    def test_router_no_direct_function_imports(self):
        source = self._read_router_source()
        assert "from app.modules.faculty_copilot.service import" not in source

    def test_router_has_domain_validation_error_import(self):
        source = self._read_router_source()
        assert "DomainValidationError" in source

    def test_router_uses_svc_generate_lesson_plan(self):
        source = self._read_router_source()
        assert "_svc.generate_lesson_plan" in source

    def test_router_uses_svc_generate_material_pack(self):
        source = self._read_router_source()
        assert "_svc.generate_material_pack" in source

    def test_router_uses_svc_answer_faculty_question(self):
        source = self._read_router_source()
        assert "_svc.answer_faculty_question" in source

    def test_router_has_lesson_plan_route(self):
        router_mod = importlib.import_module("app.modules.faculty_copilot.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any("lesson-plan" in p for p in paths)

    def test_router_has_materials_route(self):
        router_mod = importlib.import_module("app.modules.faculty_copilot.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any("materials" in p for p in paths)

    def test_router_has_qna_route(self):
        router_mod = importlib.import_module("app.modules.faculty_copilot.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any("qna" in p for p in paths)

    def test_router_lesson_plan_catches_domain_validation_error(self):
        source = self._read_router_source()
        assert "DomainValidationError" in source
        # ensure the catch is present in all three endpoints
        assert source.count("except (ValueError, DomainValidationError)") >= 3

    def test_router_maps_errors_to_422(self):
        source = self._read_router_source()
        assert "status_code=422" in source
