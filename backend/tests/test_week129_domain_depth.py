"""W129 Domain Depth — faculty_copilot × faculty_contracts guard.

Guard: _check_faculty_has_active_contract_for_copilot
- Blocks copilot access when faculty has no active employment contract
- Blocks terminated/resigned/inactive faculty
- Fail-closed on faculty_contracts lookup failure
- Guard fires before AI service calls for lesson plan, materials, and QnA
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty_copilot.schemas import (
    FacultyQnARequestSchema,
    LessonPlanRequestSchema,
    MaterialPackRequestSchema,
)
from app.modules.faculty_copilot.service import (
    _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES,
    _check_faculty_has_active_contract_for_copilot,
    answer_faculty_question,
    generate_lesson_plan,
    generate_material_pack,
)


_TENANT = 91
_FACULTY_ID = "FAC-001"


def _contract(status: str, faculty_id: str = _FACULTY_ID) -> dict:
    return {"id": "fc-1", "faculty_id": faculty_id, "status": status}


def _alt_contract(status: str, faculty_id: str = _FACULTY_ID) -> dict:
    return {"id": "fc-2", "employee_id": faculty_id, "contract_status": status}


def _ai_answer(question: str = "ok") -> dict[str, object]:
    return {
        "question": question,
        "summary": "generated",
        "insights": [],
        "sources": [],
        "warnings": [],
        "recommendations": [],
    }


def _lesson_payload(**overrides) -> LessonPlanRequestSchema:
    data = {
        "faculty_id": _FACULTY_ID,
        "course_title": "Data Structures",
        "topic": "Balanced Trees",
        "duration_minutes": 90,
        "learning_objectives": ["Explain AVL rotations"],
    }
    data.update(overrides)
    return LessonPlanRequestSchema(**data)


def _materials_payload(**overrides) -> MaterialPackRequestSchema:
    data = {
        "faculty_id": _FACULTY_ID,
        "course_title": "Databases",
        "topic": "Query Optimization",
        "material_type": "slides",
    }
    data.update(overrides)
    return MaterialPackRequestSchema(**data)


def _qna_payload(**overrides) -> FacultyQnARequestSchema:
    data = {
        "faculty_id": _FACULTY_ID,
        "course_title": "Operating Systems",
        "question": "How should I explain deadlock prevention?",
    }
    data.update(overrides)
    return FacultyQnARequestSchema(**data)


class TestW129Constants:
    def test_active_statuses_is_frozenset(self):
        assert isinstance(_FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_expired_not_in_statuses(self):
        assert "expired" not in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_inactive_not_in_statuses(self):
        assert "inactive" not in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_pending_not_in_statuses(self):
        assert "pending" not in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES

    def test_statuses_nonempty(self):
        assert len(_FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES) >= 1

    def test_statuses_lowercase(self):
        for status in _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES:
            assert status == status.lower()

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _FACULTY_COPILOT_ACTIVE_CONTRACT_STATUSES.add("temp")  # type: ignore[attr-defined]


class TestW129GuardSignature:
    def test_guard_callable(self):
        assert callable(_check_faculty_has_active_contract_for_copilot)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            _check_faculty_has_active_contract_for_copilot(_TENANT, _FACULTY_ID)  # type: ignore[call-arg]

    def test_guard_requires_faculty_id(self):
        with pytest.raises(TypeError):
            _check_faculty_has_active_contract_for_copilot(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        result = _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )
        assert result is None

    def test_guard_strips_whitespace_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id="  FAC-001  ",
        )

    def test_guard_queries_faculty_contracts_entity(self, monkeypatch):
        queried = []

        def mock_list(entity_type, tenant_id):
            queried.append(entity_type)
            return [_contract("active")]

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            mock_list,
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )
        assert "faculty_contracts" in queried


class TestW129GuardFailures:
    def test_blocks_when_no_contracts(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_blocks_when_wrong_faculty_contracts(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active", faculty_id="other")],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_blocks_when_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_blocks_when_contract_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_blocks_when_contract_inactive(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("inactive")],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_error_contains_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )
        assert _FACULTY_ID in str(exc_info.value)


class TestW129FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("db offline")

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="lookup failed"):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_fail_closed_on_connection_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )

    def test_fail_closed_error_includes_faculty_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise OSError("network down")

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )
        assert _FACULTY_ID in str(exc_info.value)

    def test_fail_closed_no_open_fallback(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise ValueError("bad data")

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )
        assert call_count == [1]


class TestW129EntryPoints:
    def test_lesson_plan_guard_fires_before_ai_call(self, monkeypatch):
        guard_calls = []
        ai_calls = []

        def mock_guard(*, tenant_id, faculty_id):
            guard_calls.append((tenant_id, faculty_id))

        def mock_ai(**kwargs):
            ai_calls.append(kwargs)
            return _ai_answer(kwargs["question"])

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service._check_faculty_has_active_contract_for_copilot",
            mock_guard,
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            mock_ai,
        )
        generate_lesson_plan(tenant_id=_TENANT, actor_id="actor", payload=_lesson_payload())
        assert guard_calls == [(_TENANT, _FACULTY_ID)]
        assert len(ai_calls) == 1

    def test_lesson_plan_ai_not_called_when_guard_blocks(self, monkeypatch):
        ai_calls = []

        def mock_guard(*, tenant_id, faculty_id):
            raise DomainValidationError("blocked")

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service._check_faculty_has_active_contract_for_copilot",
            mock_guard,
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            lambda **kwargs: ai_calls.append(kwargs) or _ai_answer(),
        )
        with pytest.raises(DomainValidationError):
            generate_lesson_plan(tenant_id=_TENANT, actor_id="actor", payload=_lesson_payload())
        assert ai_calls == []

    def test_materials_guard_fires_before_ai_call(self, monkeypatch):
        guard_calls = []
        ai_calls = []

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service._check_faculty_has_active_contract_for_copilot",
            lambda *, tenant_id, faculty_id: guard_calls.append((tenant_id, faculty_id)),
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            lambda **kwargs: ai_calls.append(kwargs) or _ai_answer(kwargs["question"]),
        )
        generate_material_pack(tenant_id=_TENANT, actor_id="actor", payload=_materials_payload())
        assert guard_calls == [(_TENANT, _FACULTY_ID)]
        assert len(ai_calls) == 1

    def test_qna_guard_fires_before_ai_call(self, monkeypatch):
        guard_calls = []
        ai_calls = []

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service._check_faculty_has_active_contract_for_copilot",
            lambda *, tenant_id, faculty_id: guard_calls.append((tenant_id, faculty_id)),
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            lambda **kwargs: ai_calls.append(kwargs) or _ai_answer(kwargs["question"]),
        )
        answer_faculty_question(tenant_id=_TENANT, actor_id="actor", payload=_qna_payload())
        assert guard_calls == [(_TENANT, _FACULTY_ID)]
        assert len(ai_calls) == 1

    def test_lesson_plan_succeeds_with_active_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            lambda **kwargs: _ai_answer(kwargs["question"]),
        )
        result = generate_lesson_plan(tenant_id=_TENANT, actor_id="actor", payload=_lesson_payload())
        assert "question" in result
        assert "summary" in result

    def test_qna_blocked_when_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.ai_service.answer_question",
            lambda **kwargs: _ai_answer(kwargs["question"]),
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            answer_faculty_question(tenant_id=_TENANT, actor_id="actor", payload=_qna_payload())


class TestW129BusinessInvariants:
    def test_alt_employee_id_key_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_alt_contract("active")],
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )

    def test_alt_contract_status_key_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_alt_contract("active")],
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )

    def test_multiple_contracts_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated"), _contract("active")],
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )

    def test_tenant_isolation(self, monkeypatch):
        queried_tenants = []

        def mock_list(entity_type, tenant_id):
            queried_tenants.append(tenant_id)
            if tenant_id == 1:
                return [_contract("active")]
            return []

        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            mock_list,
        )
        _check_faculty_has_active_contract_for_copilot(tenant_id=1, faculty_id=_FACULTY_ID)
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_copilot(tenant_id=2, faculty_id=_FACULTY_ID)
        assert 1 in queried_tenants and 2 in queried_tenants

    def test_status_match_case_insensitive(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("ACTIVE")],
        )
        _check_faculty_has_active_contract_for_copilot(
            tenant_id=_TENANT,
            faculty_id=_FACULTY_ID,
        )

    def test_error_message_has_copilot_context(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_copilot.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_copilot(
                tenant_id=_TENANT,
                faculty_id=_FACULTY_ID,
            )
        assert "copilot" in str(exc_info.value).lower()