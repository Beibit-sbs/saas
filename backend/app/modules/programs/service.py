import logging

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.usage.service import record_usage_event
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    delete_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)

logger = logging.getLogger("app.modules.programs")

# W44: cap on active programs per degree_type per tenant
_PROGRAM_DEGREE_TYPE_MAX_ACTIVE: dict[str, int] = {
    "bachelor": 50,
    "master": 40,
    "doctorate": 20,
    "associate": 30,
    "certificate": 80,
    "diploma": 60,
}

_ACTIVE_PROGRAM_STATUSES: frozenset[str] = frozenset({"active", "draft"})

# W44: statuses that trigger a sunset risk alert
_SUNSET_RISK_STATUSES: frozenset[str] = frozenset({"inactive", "archived"})

# W85: statuses that require at least one active degree requirement
_ACTIVATION_STATUSES: frozenset[str] = frozenset({"active"})


def _audit(tenant_id: int, action: str, actor_id: str, entity_id: object = None, detail: object = None) -> None:
    try:
        log_admin_action(tenant_id=tenant_id, action=action, actor_id=actor_id, entity_id=entity_id, detail=detail)
    except Exception:
        logger.exception("programs audit failed action=%s", action)


def _record_outcome(entity_id: object, outcome_type: str, actor_id: str) -> None:
    try:
        from app.modules.brain_core import service as brain_core_service  # noqa: PLC0415
        brain_core_service.record_dispatch_outcome(
            entity_id=entity_id,
            outcome_type=outcome_type,
            actor_id=str(actor_id),
        )
    except Exception:
        logger.exception("programs outcome failed entity_id=%s outcome=%s", entity_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("programs metric failed metric=%s", metric)


def _check_program_has_active_requirements(tenant_id: int, program_id: int) -> None:
    """Cross-entity guard: program cannot be activated without at least one active requirement.

    An active program with zero active degree requirements creates every enrolled student
    with a permanently-unsatisfiable graduation state — remaining_required_items = 0 forever,
    every student graduates without taking any courses, accreditation violation.

    HARDENING RULE: NO SILENT FALLBACK — if validation cannot complete, block the action.
    """
    try:
        requirements = list_entities_for_tenant("program_requirements", tenant_id)
    except (ValueError, KeyError) as e:
        # Entity "program_requirements" not available in entity service
        # Cannot enforce invariant without access to requirement data — must block
        raise DomainValidationError(
            f"Cannot activate program_id={program_id}: cannot verify active requirements exist. "
            "Program requirements entity service is unavailable. "
            "Cannot enforce requirement invariant without access to requirement data."
        ) from e

    # Check if any active requirement exists for this program
    active_requirements = [
        r for r in requirements
        if int(r.get("program_id") or 0) == program_id
        and str(r.get("is_active") or "").lower() in {"true", "1", "yes"}
    ]

    if not active_requirements:
        raise DomainValidationError(
            f"Cannot activate program_id={program_id}: no active degree requirements configured. "
            "A program cannot be activated without a graduation pathway. "
            "Add at least one active ProgramRequirementModel before activating."
        )



def list_programs(tenant_id: int) -> list[dict[str, object]]:
    return list_entities_for_tenant("programs", tenant_id)


def create_program(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    existing = list_entities_for_tenant("programs", tenant_id)

    # W44: count-cap guard on active programs per degree_type
    degree_type = str(payload.get("degree_type") or "").strip().lower()
    cap = _PROGRAM_DEGREE_TYPE_MAX_ACTIVE.get(degree_type, 50)
    active_count = sum(
        1 for p in existing
        if str(p.get("status") or "").strip().lower() in _ACTIVE_PROGRAM_STATUSES
        and str(p.get("degree_type") or "").strip().lower() == degree_type
    )
    if active_count >= cap:
        raise ValueError(
            f"Active program cap ({cap}) reached for degree_type '{degree_type}'"
        )

    result = create_entity_for_tenant("programs", payload, tenant_id)
    _record_outcome(result.get("id"), "program_created", str(payload.get("actor_id") or "system"))
    _metric(tenant_id, "programs_created")
    return result


def update_program(program_id: int, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    to_status = str(payload.get("status") or "").strip().lower()

    # W85: activation requires at least one active requirement
    if to_status in _ACTIVATION_STATUSES:
        _check_program_has_active_requirements(tenant_id, program_id)

    result = update_entity_for_tenant("programs", program_id, payload, tenant_id)
    if to_status in {"inactive", "archived"}:
        from app.platform.events.publisher import EventPublisher
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="programs.status.risk_detected",
            aggregate_type="program",
            aggregate_id=program_id,
            payload_json={
                "program_id": program_id,
                "to_status": to_status,
                "source_module": "programs",
            },
        )
    # W44: side-effect sunset alert for risk statuses
    if to_status in _SUNSET_RISK_STATUSES:
        _ensure_sunset_alert_record(
            tenant_id=tenant_id,
            program_id=program_id,
            program_data={
                "program_code": str(payload.get("program_code") or ""),
                "degree_type": str(payload.get("degree_type") or ""),
                "status": to_status,
            },
        )
    _record_outcome(program_id, "program_updated", str(payload.get("actor_id") or "system"))
    _metric(tenant_id, "programs_updated")
    return result


def _ensure_sunset_alert_record(
    tenant_id: int,
    program_id: int,
    program_data: dict,
) -> None:
    """Idempotent: create a program_sunset_alerts entry for inactive/archived programs."""
    src = "programs_sunset_queue"
    src_id = str(program_id)
    existing = list_entities_for_tenant("program_sunset_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == src
            and str(rec.get("source_entity_id")) == src_id
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "program_sunset_alerts",
        {
            "program_id": program_id,
            "program_code": str(program_data.get("program_code") or ""),
            "degree_type": str(program_data.get("degree_type") or ""),
            "sunset_status": str(program_data.get("status") or ""),
            "alert_status": "open",
            "integration_source": src,
            "source_entity_id": src_id,
        },
        tenant_id,
    )


def delete_program(program_id: int, tenant_id: int) -> dict[str, object]:
    return delete_entity_for_tenant("programs", program_id, tenant_id)


def get_program_consistency_report(tenant_id: int) -> dict[str, object]:
    programs = list_entities_for_tenant("programs", tenant_id)

    allowed_degree_types = {"bachelor", "master", "doctorate", "associate", "certificate", "diploma"}
    allowed_statuses = {"active", "inactive", "archived", "draft"}

    issues: list[dict[str, object]] = []
    code_counts: dict[str, int] = {}

    for program in programs:
        code_raw = program.get("program_code")
        code = str(code_raw).strip() if code_raw is not None else ""
        if code:
            code_counts[code] = code_counts.get(code, 0) + 1

    duplicate_codes = {
        code for code, count in code_counts.items() if count > 1
    }

    for program in programs:
        program_id_raw = program.get("id")
        code_raw = program.get("program_code")
        title_raw = program.get("title")
        degree_type_raw = program.get("degree_type")
        status_raw = program.get("status")

        try:
            program_id = int(program_id_raw)
        except (TypeError, ValueError):
            program_id = None

        code = str(code_raw).strip() if code_raw is not None else ""
        if not code:
            issues.append(
                {
                    "issue_type": "program_missing_code",
                    "program_id": program_id,
                }
            )
        elif code in duplicate_codes:
            issues.append(
                {
                    "issue_type": "duplicate_program_code",
                    "program_id": program_id,
                    "program_code": code,
                }
            )

        title = str(title_raw).strip() if title_raw is not None else ""
        if not title:
            issues.append({"issue_type": "program_missing_name", "program_id": program_id})

        degree_type = str(degree_type_raw).strip().lower() if degree_type_raw is not None else ""
        if degree_type not in allowed_degree_types:
            issues.append(
                {
                    "issue_type": "program_invalid_degree_type",
                    "program_id": program_id,
                    "degree_type": degree_type_raw,
                }
            )

        status = str(status_raw).strip().lower() if status_raw is not None else ""
        if status not in allowed_statuses:
            issues.append(
                {
                    "issue_type": "program_invalid_status",
                    "program_id": program_id,
                    "status": status_raw,
                }
            )

    return {
        "program_count": len(programs),
        "issue_count": len(issues),
        "issues": issues,
    }


def get_programs_brain_context(tenant_id: int) -> dict[str, object]:
    """Return aggregated brain-context snapshot for Brain Core context builder."""
    programs = list_entities_for_tenant("programs", tenant_id)
    report = get_program_consistency_report(tenant_id)
    active = sum(1 for p in programs if str(p.get("status", "")).lower() == "active")
    issue_count = int(report.get("issue_count", 0))
    return {
        "snapshot_type": "brain_context",
        "module": "programs",
        "tenant_id": tenant_id,
        "total_programs": len(programs),
        "active_programs": active,
        "inconsistency_count": issue_count,
        "programs_risk_level": "high" if issue_count > 5 else ("medium" if issue_count > 0 else "low"),
    }
