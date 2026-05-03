"""Internship Module service — Phase XLI.

FSM заявки (Application):
  APPLIED → SHORTLISTED → INTERVIEW → OFFERED → ACCEPTED
                                              → REJECTED
  APPLIED → REJECTED  (прямой отказ)
  SHORTLISTED → REJECTED

FSM контракта (Contract):
  DRAFT → SIGNED → ACTIVE → COMPLETED

Операции:
  create_posting(tenant_id, *, company_id, title, description, slots)
  apply(tenant_id, *, posting_id, student_id, cover_letter="")
  shortlist(tenant_id, *, application_id)
  schedule_interview(tenant_id, *, application_id, interview_date)
  make_offer(tenant_id, *, application_id)
  accept_offer(tenant_id, *, application_id)
  reject_application(tenant_id, *, application_id, reason="")
  create_contract(tenant_id, *, application_id, student_id, company_id, start_date, end_date)
  sign_contract(tenant_id, *, contract_id)
  activate_contract(tenant_id, *, contract_id)
  complete_contract(tenant_id, *, contract_id, grade=None)
  list_postings(tenant_id, *, company_id=None, status=None)
  list_applications(tenant_id, *, posting_id=None, student_id=None, status=None)

События:
  internship.application_submitted
  internship.offer_received
  internship.contract_signed
  internship.completed
  internship.completion_risk    (если контракт завершён без оценки)
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ─── constants ────────────────────────────────────────────────────────────────

APPLICATION_STATES = frozenset({"APPLIED", "SHORTLISTED", "INTERVIEW", "OFFERED", "ACCEPTED", "REJECTED"})
CONTRACT_STATES = frozenset({"DRAFT", "SIGNED", "ACTIVE", "COMPLETED"})

_APPLICATION_FSM: dict[str, list[str]] = {
    "APPLIED":     ["SHORTLISTED", "REJECTED"],
    "SHORTLISTED": ["INTERVIEW", "REJECTED"],
    "INTERVIEW":   ["OFFERED", "REJECTED"],
    "OFFERED":     ["ACCEPTED", "REJECTED"],
}

_CONTRACT_FSM: dict[str, list[str]] = {
    "DRAFT":  ["SIGNED"],
    "SIGNED": ["ACTIVE"],
    "ACTIVE": ["COMPLETED"],
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fire(tenant_id: int, event_type: str, payload: dict) -> None:
    try:
        pub = EventPublisher(tenant_id=tenant_id)
        pub.publish_event(event_type=event_type, payload=payload)
    except Exception:
        pass


def _validate_tenant(tenant_id: int) -> None:
    if not tenant_id or tenant_id <= 0:
        raise ValueError("tenant_id must be a positive integer")


def _get_application(tenant_id: int, application_id: str) -> dict:
    apps = list_entities_for_tenant("internship_applications", tenant_id=tenant_id)
    app = next((a for a in apps if str(a.get("id", "")) == str(application_id)), None)
    if app is None:
        raise LookupError(f"Application {application_id} not found")
    return app


def _get_contract(tenant_id: int, contract_id: str) -> dict:
    contracts = list_entities_for_tenant("internship_contracts", tenant_id=tenant_id)
    contract = next((c for c in contracts if str(c.get("id", "")) == str(contract_id)), None)
    if contract is None:
        raise LookupError(f"Contract {contract_id} not found")
    return contract


def _assert_app_transition(application: dict, target: str) -> None:
    current = application.get("status", "")
    allowed = _APPLICATION_FSM.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"Cannot transition application from '{current}' to '{target}'. Allowed: {allowed}"
        )


def _assert_contract_transition(contract: dict, target: str) -> None:
    current = contract.get("status", "")
    allowed = _CONTRACT_FSM.get(current, [])
    if target not in allowed:
        raise ValueError(
            f"Cannot transition contract from '{current}' to '{target}'. Allowed: {allowed}"
        )


# ─── postings ─────────────────────────────────────────────────────────────────

def create_posting(
    tenant_id: int,
    *,
    company_id: str,
    title: str,
    description: str = "",
    slots: int = 1,
) -> dict:
    _validate_tenant(tenant_id)
    if not company_id:
        raise ValueError("company_id is required")
    if not title:
        raise ValueError("title is required")
    if slots < 1:
        raise ValueError("slots must be at least 1")

    posting = create_entity_for_tenant(
        "internship_postings",
        tenant_id=tenant_id,
        data={
            "company_id": company_id,
            "title": title,
            "description": description,
            "slots": slots,
            "status": "OPEN",
            "created_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )
    return {"posting_id": posting.get("id"), "status": "OPEN", "slots": slots}


# ─── applications ─────────────────────────────────────────────────────────────

def apply(
    tenant_id: int,
    *,
    posting_id: str,
    student_id: str,
    cover_letter: str = "",
) -> dict:
    _validate_tenant(tenant_id)
    if not posting_id:
        raise ValueError("posting_id is required")
    if not student_id:
        raise ValueError("student_id is required")

    application = create_entity_for_tenant(
        "internship_applications",
        tenant_id=tenant_id,
        data={
            "posting_id": posting_id,
            "student_id": student_id,
            "cover_letter": cover_letter,
            "status": "APPLIED",
            "applied_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )

    _fire(tenant_id, "internship.application_submitted", {
        "application_id": application.get("id"),
        "posting_id": posting_id,
        "student_id": student_id,
        "tenant_id": tenant_id,
    })

    return {"application_id": application.get("id"), "status": "APPLIED"}


def shortlist(tenant_id: int, *, application_id: str) -> dict:
    _validate_tenant(tenant_id)
    app = _get_application(tenant_id, application_id)
    _assert_app_transition(app, "SHORTLISTED")
    return {"application_id": application_id, "status": "SHORTLISTED"}


def schedule_interview(
    tenant_id: int,
    *,
    application_id: str,
    interview_date: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not interview_date:
        raise ValueError("interview_date is required")
    app = _get_application(tenant_id, application_id)
    _assert_app_transition(app, "INTERVIEW")

    create_entity_for_tenant(
        "internship_interviews",
        tenant_id=tenant_id,
        data={
            "application_id": application_id,
            "interview_date": interview_date,
            "tenant_id": tenant_id,
        },
    )
    return {"application_id": application_id, "status": "INTERVIEW", "interview_date": interview_date}


def make_offer(tenant_id: int, *, application_id: str) -> dict:
    _validate_tenant(tenant_id)
    app = _get_application(tenant_id, application_id)
    _assert_app_transition(app, "OFFERED")

    _fire(tenant_id, "internship.offer_received", {
        "application_id": application_id,
        "student_id": app.get("student_id"),
        "posting_id": app.get("posting_id"),
        "tenant_id": tenant_id,
    })

    return {"application_id": application_id, "status": "OFFERED"}


def accept_offer(tenant_id: int, *, application_id: str) -> dict:
    _validate_tenant(tenant_id)
    app = _get_application(tenant_id, application_id)
    _assert_app_transition(app, "ACCEPTED")
    return {"application_id": application_id, "status": "ACCEPTED"}


def reject_application(
    tenant_id: int,
    *,
    application_id: str,
    reason: str = "",
) -> dict:
    _validate_tenant(tenant_id)
    app = _get_application(tenant_id, application_id)
    _assert_app_transition(app, "REJECTED")
    return {"application_id": application_id, "status": "REJECTED", "reason": reason}


# ─── contracts ────────────────────────────────────────────────────────────────

def create_contract(
    tenant_id: int,
    *,
    application_id: str,
    student_id: str,
    company_id: str,
    start_date: str,
    end_date: str,
) -> dict:
    _validate_tenant(tenant_id)
    if not student_id:
        raise ValueError("student_id is required")
    if not company_id:
        raise ValueError("company_id is required")
    if not start_date or not end_date:
        raise ValueError("start_date and end_date are required")

    contract = create_entity_for_tenant(
        "internship_contracts",
        tenant_id=tenant_id,
        data={
            "application_id": application_id,
            "student_id": student_id,
            "company_id": company_id,
            "start_date": start_date,
            "end_date": end_date,
            "status": "DRAFT",
            "created_at": _utc_now(),
            "tenant_id": tenant_id,
        },
    )
    return {"contract_id": contract.get("id"), "status": "DRAFT"}


def sign_contract(tenant_id: int, *, contract_id: str) -> dict:
    _validate_tenant(tenant_id)
    contract = _get_contract(tenant_id, contract_id)
    _assert_contract_transition(contract, "SIGNED")

    _fire(tenant_id, "internship.contract_signed", {
        "contract_id": contract_id,
        "student_id": contract.get("student_id"),
        "company_id": contract.get("company_id"),
        "tenant_id": tenant_id,
    })

    return {"contract_id": contract_id, "status": "SIGNED"}


def activate_contract(tenant_id: int, *, contract_id: str) -> dict:
    _validate_tenant(tenant_id)
    contract = _get_contract(tenant_id, contract_id)
    _assert_contract_transition(contract, "ACTIVE")
    return {"contract_id": contract_id, "status": "ACTIVE"}


def complete_contract(
    tenant_id: int,
    *,
    contract_id: str,
    grade: float | None = None,
) -> dict:
    _validate_tenant(tenant_id)
    if grade is not None and not (0.0 <= grade <= 100.0):
        raise ValueError("grade must be between 0 and 100")

    contract = _get_contract(tenant_id, contract_id)
    _assert_contract_transition(contract, "COMPLETED")

    _fire(tenant_id, "internship.completed", {
        "contract_id": contract_id,
        "student_id": contract.get("student_id"),
        "company_id": contract.get("company_id"),
        "grade": grade,
        "tenant_id": tenant_id,
    })

    if grade is None:
        _fire(tenant_id, "internship.completion_risk", {
            "contract_id": contract_id,
            "student_id": contract.get("student_id"),
            "reason": "No grade assigned at completion",
            "tenant_id": tenant_id,
        })

    return {
        "contract_id": contract_id,
        "status": "COMPLETED",
        "grade": grade,
        "completion_risk": grade is None,
    }


# ─── list helpers ─────────────────────────────────────────────────────────────

def list_postings(
    tenant_id: int,
    *,
    company_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("internship_postings", tenant_id=tenant_id)
    if company_id:
        rows = [r for r in rows if str(r.get("company_id", "")) == str(company_id)]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def list_applications(
    tenant_id: int,
    *,
    posting_id: str | None = None,
    student_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    _validate_tenant(tenant_id)
    rows = list_entities_for_tenant("internship_applications", tenant_id=tenant_id)
    if posting_id:
        rows = [r for r in rows if str(r.get("posting_id", "")) == str(posting_id)]
    if student_id:
        rows = [r for r in rows if str(r.get("student_id", "")) == str(student_id)]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows
