from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.student_life.schemas import (
    AccessibilitySupportCreateSchema,
    AccessibilitySupportSchema,
    CounselingCaseCreateSchema,
    CounselingCaseSchema,
    DisciplinaryCaseCreateSchema,
    DisciplinaryCaseSchema,
    StudentLifeHealthSnapshotSchema,
    WellbeingCheckinCreateSchema,
    WellbeingCheckinSchema,
)
from app.modules.university_core.tenant_entity_service import create_entity_for_tenant, list_entities_for_tenant


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="student_life",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_counseling_cases(tenant_id: int) -> list[CounselingCaseSchema]:
    rows = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
    return [CounselingCaseSchema.model_validate(r) for r in rows]


def create_counseling_case(tenant_id: int, request: CounselingCaseCreateSchema, actor: str) -> CounselingCaseSchema:
    created = create_entity_for_tenant(
        "student_life_counseling_cases",
        {
            "case_code": request.case_code.strip(),
            "student_id": request.student_id.strip(),
            "concern_type": request.concern_type.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "counseling_case", "create"),
        path="/internal/student-life/counseling-cases",
        metadata={"resource_id": str(created.get("id")), "case_code": request.case_code},
        tenant_id=tenant_id,
    )
    return CounselingCaseSchema.model_validate(created)


def list_wellbeing_checkins(tenant_id: int) -> list[WellbeingCheckinSchema]:
    rows = list_entities_for_tenant("student_life_wellbeing_checkins", tenant_id)
    return [WellbeingCheckinSchema.model_validate(r) for r in rows]


def create_wellbeing_checkin(
    tenant_id: int,
    request: WellbeingCheckinCreateSchema,
    actor: str,
) -> WellbeingCheckinSchema:
    created = create_entity_for_tenant(
        "student_life_wellbeing_checkins",
        {
            "student_id": request.student_id.strip(),
            "wellbeing_score": int(request.wellbeing_score),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "wellbeing_checkin", "create"),
        path="/internal/student-life/wellbeing-checkins",
        metadata={"resource_id": str(created.get("id")), "student_id": request.student_id},
        tenant_id=tenant_id,
    )
    return WellbeingCheckinSchema.model_validate(created)


def list_accessibility_supports(tenant_id: int) -> list[AccessibilitySupportSchema]:
    rows = list_entities_for_tenant("student_life_accessibility_supports", tenant_id)
    return [AccessibilitySupportSchema.model_validate(r) for r in rows]


def create_accessibility_support(
    tenant_id: int,
    request: AccessibilitySupportCreateSchema,
    actor: str,
) -> AccessibilitySupportSchema:
    created = create_entity_for_tenant(
        "student_life_accessibility_supports",
        {
            "support_code": request.support_code.strip(),
            "student_id": request.student_id.strip(),
            "support_type": request.support_type.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "accessibility_support", "create"),
        path="/internal/student-life/accessibility-supports",
        metadata={"resource_id": str(created.get("id")), "support_code": request.support_code},
        tenant_id=tenant_id,
    )
    return AccessibilitySupportSchema.model_validate(created)


def list_disciplinary_cases(tenant_id: int) -> list[DisciplinaryCaseSchema]:
    rows = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)
    return [DisciplinaryCaseSchema.model_validate(r) for r in rows]


def create_disciplinary_case(
    tenant_id: int,
    request: DisciplinaryCaseCreateSchema,
    actor: str,
) -> DisciplinaryCaseSchema:
    created = create_entity_for_tenant(
        "student_life_disciplinary_cases",
        {
            "incident_code": request.incident_code.strip(),
            "student_id": request.student_id.strip(),
            "incident_type": request.incident_type.strip(),
            "severity": request.severity.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("student_life", "disciplinary_case", "create"),
        path="/internal/student-life/disciplinary-cases",
        metadata={"resource_id": str(created.get("id")), "incident_code": request.incident_code},
        tenant_id=tenant_id,
    )
    return DisciplinaryCaseSchema.model_validate(created)


def get_student_life_health_snapshot(tenant_id: int) -> StudentLifeHealthSnapshotSchema:
    counseling_rows = list_entities_for_tenant("student_life_counseling_cases", tenant_id)
    wellbeing_rows = list_entities_for_tenant("student_life_wellbeing_checkins", tenant_id)
    accessibility_rows = list_entities_for_tenant("student_life_accessibility_supports", tenant_id)
    disciplinary_rows = list_entities_for_tenant("student_life_disciplinary_cases", tenant_id)

    open_counseling_cases = 0
    for row in counseling_rows:
        if str(row.get("status") or "") in {"open", "in_progress"}:
            open_counseling_cases += 1

    at_risk_wellbeing = 0
    for row in wellbeing_rows:
        status = str(row.get("status") or "")
        score = row.get("wellbeing_score")
        is_low_score = isinstance(score, int) and score <= 40
        if status == "at_risk" or is_low_score:
            at_risk_wellbeing += 1

    active_accessibility_supports = 0
    for row in accessibility_rows:
        if str(row.get("status") or "") in {"requested", "active"}:
            active_accessibility_supports += 1

    unresolved_disciplinary_cases = 0
    for row in disciplinary_rows:
        if str(row.get("status") or "") in {"reported", "under_review", "appealed"}:
            unresolved_disciplinary_cases += 1

    return StudentLifeHealthSnapshotSchema(
        tenant_id=tenant_id,
        counseling_cases_total=len(counseling_rows),
        open_counseling_cases=open_counseling_cases,
        wellbeing_checkins_total=len(wellbeing_rows),
        at_risk_wellbeing_checkins=at_risk_wellbeing,
        accessibility_supports_total=len(accessibility_rows),
        active_accessibility_supports=active_accessibility_supports,
        disciplinary_cases_total=len(disciplinary_rows),
        unresolved_disciplinary_cases=unresolved_disciplinary_cases,
    )