"""W90 — research_ethics: approval requires PI active faculty + active contract.

Behavioral tests for cross-entity transition guard in update_ethics_review_status().
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema
from app.modules.research_ethics.service import update_ethics_review_status



def _make_review(*, status: str = "under_review", pi_id: str = "FAC-1") -> dict:
    return {
        "id": 77,
        "review_code": "RE-77",
        "project_title": "Genome Study",
        "principal_investigator_id": pi_id,
        "review_type": "irb",
        "status": status,
        "risk_level": "minimal",
    }



def _make_faculty(*, faculty_id: str = "FAC-1", status: str = "active") -> dict:
    return {
        "id": 1,
        "faculty_id": faculty_id,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "department": "Research",
        "email": "ada@example.edu",
        "status": status,
    }



def _make_contract(*, faculty_id: str = "FAC-1", status: str = "active") -> dict:
    return {
        "id": 9,
        "faculty_id": faculty_id,
        "contract_type": "full_time",
        "status": status,
    }



def test_w90_guard_function_exists_and_callable():
    from app.modules.research_ethics.service import _check_pi_eligibility_for_approval

    assert callable(_check_pi_eligibility_for_approval)



def test_w90_constants_exist_and_contain_expected_values():
    from app.modules.research_ethics.service import (
        _APPROVAL_TRANSITION_STATUSES,
        _REQUIRED_PI_CONTRACT_STATUSES,
        _REQUIRED_PI_FACULTY_STATUSES,
    )

    assert isinstance(_APPROVAL_TRANSITION_STATUSES, frozenset)
    assert "approved" in _APPROVAL_TRANSITION_STATUSES

    assert isinstance(_REQUIRED_PI_FACULTY_STATUSES, frozenset)
    assert "active" in _REQUIRED_PI_FACULTY_STATUSES

    assert isinstance(_REQUIRED_PI_CONTRACT_STATUSES, frozenset)
    assert "active" in _REQUIRED_PI_CONTRACT_STATUSES



def test_w90_approval_blocked_when_pi_missing_from_faculty_registry():
    review = _make_review(status="under_review", pi_id="FAC-MISSING")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            return []
        if name == "faculty_contracts":
            return []
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="not found in faculty registry"):
            update_ethics_review_status(
                tenant_id=1,
                review_id=77,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
            )



def test_w90_approval_blocked_when_pi_faculty_status_inactive():
    review = _make_review(status="under_review", pi_id="FAC-1")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            return [_make_faculty(faculty_id="FAC-1", status="inactive")]
        if name == "faculty_contracts":
            return [_make_contract(faculty_id="FAC-1", status="active")]
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="faculty status"):
            update_ethics_review_status(
                tenant_id=1,
                review_id=77,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
            )



def test_w90_approval_blocked_when_pi_has_no_active_contract():
    review = _make_review(status="under_review", pi_id="FAC-1")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            return [_make_faculty(faculty_id="FAC-1", status="active")]
        if name == "faculty_contracts":
            return [_make_contract(faculty_id="FAC-1", status="terminated")]
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="contract statuses"):
            update_ethics_review_status(
                tenant_id=1,
                review_id=77,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
            )



def test_w90_approval_allowed_when_pi_is_active_with_active_contract():
    review = _make_review(status="under_review", pi_id="FAC-1")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            return [_make_faculty(faculty_id="FAC-1", status="active")]
        if name == "faculty_contracts":
            return [_make_contract(faculty_id="FAC-1", status="active")]
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities), patch(
        "app.modules.research_ethics.service.update_entity_for_tenant",
        side_effect=lambda *_args, **_kwargs: {**review, "status": "approved"},
    ):
        updated = update_ethics_review_status(
            tenant_id=1,
            review_id=77,
            request=EthicsReviewStatusUpdateSchema(status="approved"),
        )

    assert updated["status"] == "approved"



def test_w90_non_approval_transition_skips_cross_entity_queries():
    review = _make_review(status="pending", pi_id="FAC-1")

    call_log: list[str] = []

    def _list_entities(name: str, _tenant_id: int):
        call_log.append(name)
        if name == "ethics_reviews":
            return [review]
        if name in {"faculty", "faculty_contracts"}:
            raise AssertionError("Cross-entity lookup must not run for non-approval transition")
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities), patch(
        "app.modules.research_ethics.service.update_entity_for_tenant",
        side_effect=lambda *_args, **_kwargs: {**review, "status": "under_review"},
    ):
        updated = update_ethics_review_status(
            tenant_id=1,
            review_id=77,
            request=EthicsReviewStatusUpdateSchema(status="under_review"),
        )

    assert updated["status"] == "under_review"
    assert call_log == ["ethics_reviews"]



def test_w90_no_silent_fallback_when_faculty_query_fails():
    review = _make_review(status="under_review", pi_id="FAC-1")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            raise RuntimeError("faculty store down")
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="faculty lookup failed"):
            update_ethics_review_status(
                tenant_id=1,
                review_id=77,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
            )



def test_w90_no_silent_fallback_when_contract_query_fails():
    review = _make_review(status="under_review", pi_id="FAC-1")

    def _list_entities(name: str, _tenant_id: int):
        if name == "ethics_reviews":
            return [review]
        if name == "faculty":
            return [_make_faculty(faculty_id="FAC-1", status="active")]
        if name == "faculty_contracts":
            raise RuntimeError("contracts store down")
        return []

    with patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            update_ethics_review_status(
                tenant_id=1,
                review_id=77,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
            )
