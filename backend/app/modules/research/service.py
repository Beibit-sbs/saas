from __future__ import annotations

from datetime import date

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.research.schemas import (
    ResearchExperimentCreateSchema,
    ResearchExperimentSchema,
    ResearchExperimentStatusUpdateSchema,
    ResearchGrantCreateSchema,
    ResearchGrantSchema,
    ResearchGrantStatus,
    ResearchGrantStatusUpdateSchema,
    ResearchHealthSnapshotSchema,
    ResearchIpAssetCreateSchema,
    ResearchIpAssetSchema,
    ResearchLabCreateSchema,
    ResearchLabSchema,
    ResearchLabStatusUpdateSchema,
    ResearchPublicationCreateSchema,
    ResearchPublicationSchema,
    ResearchPublicationStatus,
    ResearchPublicationStatusUpdateSchema,
)
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


# W110: Grant statuses that count as "active" for publication authorship check
_GRANT_ACTIVE_FOR_PUBLICATION: frozenset[str] = frozenset({"active", "planned", "submitted"})


_RESEARCH_GRANT_STATUS_MAX_ACTIVE: dict[str, int] = {
    "planned": 250,
    "active": 180,
    "submitted": 120,
    "delayed": 80,
    "closed": 2000,
}

_ACTIVE_RESEARCH_GRANT_STATUSES = frozenset({"planned", "active", "submitted", "delayed"})
_GRANT_DELAY_RISK_STATUSES = frozenset({"delayed"})


def _check_author_has_active_grant(
    *,
    tenant_id: int,
    lead_author_id: str,
) -> None:
    """Cross-entity guard: research_publications × research_grants by lead_author_id / pi_faculty_id.

    A publication may only be created if the lead author has at least one
    active research grant (status: active, planned, submitted). Creating
    publications without funding evidence produces phantom research output,
    corrupts Brain Core research KPIs, and misrepresents institutional
    research productivity metrics.

    FAIL-CLOSED: If grant lookup fails (any exception), publication creation
    is BLOCKED. Cannot verify funding without grant data.
    """
    try:
        all_grants = list_entities_for_tenant("research_grants", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Publication creation blocked for lead_author_id='{lead_author_id}': "
            f"research_grants lookup failed \u2014 {exc}. Cannot verify active grant."
        ) from exc

    has_active_grant = any(
        str(g.get("pi_faculty_id") or "").strip().lower()
        == str(lead_author_id).strip().lower()
        and str(g.get("status") or "").strip().lower() in _GRANT_ACTIVE_FOR_PUBLICATION
        for g in all_grants
    )

    if not has_active_grant:
        raise DomainValidationError(
            f"Publication creation blocked for lead_author_id='{lead_author_id}': "
            f"no active research grant found (required statuses: {sorted(_GRANT_ACTIVE_FOR_PUBLICATION)}). "
            f"Publications must be backed by funded research to prevent phantom output."
        )


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="research",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def _parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _safe_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def list_research_grants(tenant_id: int, status: ResearchGrantStatus | None = None) -> list[ResearchGrantSchema]:
    rows = list_entities_for_tenant("research_grants", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [ResearchGrantSchema.model_validate(r) for r in rows]


def create_research_grant(tenant_id: int, request: ResearchGrantCreateSchema, actor: str) -> ResearchGrantSchema:
    requested_status = str(request.status).strip().lower()
    active_grants = [
        row
        for row in list_entities_for_tenant("research_grants", tenant_id)
        if str(row.get("status") or "").strip().lower() in _ACTIVE_RESEARCH_GRANT_STATUSES
    ]
    grant_cap = _RESEARCH_GRANT_STATUS_MAX_ACTIVE.get(requested_status, 250)
    if len(active_grants) >= grant_cap:
        raise ValueError("research_grant active cap reached")

    created = create_entity_for_tenant(
        "research_grants",
        {
            "grant_code": request.grant_code.strip(),
            "title": request.title.strip(),
            "pi_faculty_id": request.pi_faculty_id.strip(),
            "deadline": request.deadline.isoformat(),
            "funding_amount": float(request.funding_amount),
            "status": request.status,
            "sponsor_notes": (request.sponsor_notes or "").strip() or None,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "grant", "create"),
        path="/internal/research/grants",
        metadata={"resource_id": str(created.get("id")), "grant_code": request.grant_code},
        tenant_id=tenant_id,
    )
    return ResearchGrantSchema.model_validate(created)


# Max active (draft/submitted) publications per lead_author_id per status
_PUBLICATION_STATUS_MAX_ACTIVE: dict[str, int] = {
    "draft": 3,
    "submitted": 2,
    "stalled": 1,
    "published": 20,
}


def _ensure_publication_review_record(
    tenant_id: int,
    publication_id: int,
    publication_data: dict,
) -> None:
    """Idempotent: create a publication_review_records entity when publication transitions to submitted."""
    existing = list_entities_for_tenant("publication_review_records", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "research_submission"
            and str(rec.get("source_entity_id")) == str(publication_id)
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "publication_review_records",
        {
            "publication_id": publication_id,
            "publication_code": str(publication_data.get("publication_code") or ""),
            "lead_author_id": str(publication_data.get("lead_author_id") or ""),
            "target_venue": str(publication_data.get("target_venue") or ""),
            "status": "under_review",
            "integration_source": "research_submission",
            "source_entity_id": str(publication_id),
        },
        tenant_id,
    )


def list_research_publications(
    tenant_id: int,
    status: ResearchPublicationStatus | None = None,
) -> list[ResearchPublicationSchema]:
    rows = list_entities_for_tenant("research_publications", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [ResearchPublicationSchema.model_validate(r) for r in rows]


def create_research_publication(
    tenant_id: int,
    request: ResearchPublicationCreateSchema,
    actor: str,
) -> ResearchPublicationSchema:
    # W110: Cross-entity guard — author must have active grant before publication
    _check_author_has_active_grant(
        tenant_id=tenant_id,
        lead_author_id=request.lead_author_id,
    )

    # Enforce cap: max active publications per author per status
    _ACTIVE_STATUSES = {"draft", "submitted", "stalled"}
    max_active = _PUBLICATION_STATUS_MAX_ACTIVE.get(request.status, 2)
    existing_rows = list_entities_for_tenant("research_publications", tenant_id)
    active_count = sum(
        1
        for r in existing_rows
        if str(r.get("lead_author_id") or "") == request.lead_author_id
        and str(r.get("status") or "") == request.status
        and str(r.get("status") or "") in _ACTIVE_STATUSES
    )
    if active_count >= max_active:
        raise ValueError(
            f"lead_author_id={request.lead_author_id} already has {active_count}"
            f" '{request.status}' publications; max={max_active}"
        )

    created = create_entity_for_tenant(
        "research_publications",
        {
            "publication_code": request.publication_code.strip(),
            "title": request.title.strip(),
            "lead_author_id": request.lead_author_id.strip(),
            "target_venue": request.target_venue.strip(),
            "last_activity_days": int(request.last_activity_days),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "publication", "create"),
        path="/internal/research/publications",
        metadata={"resource_id": str(created.get("id")), "publication_code": request.publication_code},
        tenant_id=tenant_id,
    )
    return ResearchPublicationSchema.model_validate(created)


def list_research_labs(tenant_id: int) -> list[ResearchLabSchema]:
    rows = list_entities_for_tenant("research_labs", tenant_id)
    return [ResearchLabSchema.model_validate(r) for r in rows]


def create_research_lab(tenant_id: int, request: ResearchLabCreateSchema, actor: str) -> ResearchLabSchema:
    created = create_entity_for_tenant(
        "research_labs",
        {
            "lab_code": request.lab_code.strip(),
            "name": request.name.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "lab", "create"),
        path="/internal/research/labs",
        metadata={"resource_id": str(created.get("id")), "lab_code": request.lab_code},
        tenant_id=tenant_id,
    )
    return ResearchLabSchema.model_validate(created)


def list_research_ip_assets(tenant_id: int) -> list[ResearchIpAssetSchema]:
    rows = list_entities_for_tenant("research_ip_assets", tenant_id)
    return [ResearchIpAssetSchema.model_validate(r) for r in rows]


def create_research_ip_asset(
    tenant_id: int,
    request: ResearchIpAssetCreateSchema,
    actor: str,
) -> ResearchIpAssetSchema:
    created = create_entity_for_tenant(
        "research_ip_assets",
        {
            "asset_code": request.asset_code.strip(),
            "title": request.title.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "ip_asset", "create"),
        path="/internal/research/ip-assets",
        metadata={"resource_id": str(created.get("id")), "asset_code": request.asset_code},
        tenant_id=tenant_id,
    )
    return ResearchIpAssetSchema.model_validate(created)


def list_research_experiments(tenant_id: int) -> list[ResearchExperimentSchema]:
    rows = list_entities_for_tenant("research_experiments", tenant_id)
    return [ResearchExperimentSchema.model_validate(r) for r in rows]


def create_research_experiment(
    tenant_id: int,
    request: ResearchExperimentCreateSchema,
    actor: str,
) -> ResearchExperimentSchema:
    created = create_entity_for_tenant(
        "research_experiments",
        {
            "experiment_code": request.experiment_code.strip(),
            "title": request.title.strip(),
            "lab_code": request.lab_code.strip(),
            "principal_investigator_id": request.principal_investigator_id.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "experiment", "create"),
        path="/internal/research/experiments",
        metadata={"resource_id": str(created.get("id")), "experiment_code": request.experiment_code},
        tenant_id=tenant_id,
    )
    return ResearchExperimentSchema.model_validate(created)


def get_research_grant(tenant_id: int, grant_id: int) -> ResearchGrantSchema:
    rows = list_entities_for_tenant("research_grants", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == grant_id), None)
    if row is None:
        raise ValueError(f"grant {grant_id} not found")
    return ResearchGrantSchema.model_validate(row)


def update_research_grant_status(
    tenant_id: int,
    grant_id: int,
    request: ResearchGrantStatusUpdateSchema,
    actor: str,
) -> ResearchGrantSchema:
    rows = list_entities_for_tenant("research_grants", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == grant_id), None)
    if existing is None:
        raise ValueError(f"grant {grant_id} not found")
    updated = update_entity_for_tenant("research_grants", grant_id, {**existing, "status": request.status}, tenant_id)
    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "grant", "status_update"),
        path=f"/internal/research/grants/{grant_id}/status",
        metadata={"resource_id": str(grant_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    if str(request.status).strip().lower() in _GRANT_DELAY_RISK_STATUSES:
        _ensure_grant_delay_alert_record(tenant_id=tenant_id, grant_id=grant_id, grant_data=updated)
    return ResearchGrantSchema.model_validate(updated)


def _ensure_grant_delay_alert_record(tenant_id: int, grant_id: int, grant_data: dict[str, object]) -> None:
    existing = list_entities_for_tenant("research_grant_delay_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "research_grant_delay_queue"
            and str(rec.get("source_entity_id")) == str(grant_id)
        ):
            return

    create_entity_for_tenant(
        "research_grant_delay_alerts",
        {
            "grant_id": grant_id,
            "grant_code": str(grant_data.get("grant_code") or ""),
            "pi_faculty_id": str(grant_data.get("pi_faculty_id") or ""),
            "status": str(grant_data.get("status") or "delayed"),
            "alert_status": "active",
            "integration_source": "research_grant_delay_queue",
            "source_entity_id": str(grant_id),
        },
        tenant_id,
    )

    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.research.grant_delay_risk_detected",
        aggregate_type="research_grant",
        aggregate_id=grant_id,
        payload_json={
            "grant_id": grant_id,
            "grant_code": str(grant_data.get("grant_code") or ""),
            "pi_faculty_id": str(grant_data.get("pi_faculty_id") or ""),
            "tenant_id": tenant_id,
        },
    )


def get_research_publication(tenant_id: int, publication_id: int) -> ResearchPublicationSchema:
    rows = list_entities_for_tenant("research_publications", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == publication_id), None)
    if row is None:
        raise ValueError(f"publication {publication_id} not found")
    return ResearchPublicationSchema.model_validate(row)


def update_research_publication_status(
    tenant_id: int,
    publication_id: int,
    request: ResearchPublicationStatusUpdateSchema,
    actor: str,
) -> ResearchPublicationSchema:
    rows = list_entities_for_tenant("research_publications", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == publication_id), None)
    if existing is None:
        raise ValueError(f"publication {publication_id} not found")
    updated = update_entity_for_tenant("research_publications", publication_id, {**existing, "status": request.status}, tenant_id)
    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "publication", "status_update"),
        path=f"/internal/research/publications/{publication_id}/status",
        metadata={"resource_id": str(publication_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    if request.status == "submitted":
        _ensure_publication_review_record(tenant_id, publication_id, updated)
    return ResearchPublicationSchema.model_validate(updated)


def get_research_lab(tenant_id: int, lab_id: int) -> ResearchLabSchema:
    rows = list_entities_for_tenant("research_labs", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == lab_id), None)
    if row is None:
        raise ValueError(f"lab {lab_id} not found")
    return ResearchLabSchema.model_validate(row)


def update_research_lab_status(
    tenant_id: int,
    lab_id: int,
    request: ResearchLabStatusUpdateSchema,
    actor: str,
) -> ResearchLabSchema:
    rows = list_entities_for_tenant("research_labs", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == lab_id), None)
    if existing is None:
        raise ValueError(f"lab {lab_id} not found")
    updated = update_entity_for_tenant("research_labs", lab_id, {**existing, "status": request.status}, tenant_id)
    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "lab", "status_update"),
        path=f"/internal/research/labs/{lab_id}/status",
        metadata={"resource_id": str(lab_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return ResearchLabSchema.model_validate(updated)


def get_research_experiment(tenant_id: int, experiment_id: int) -> ResearchExperimentSchema:
    rows = list_entities_for_tenant("research_experiments", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == experiment_id), None)
    if row is None:
        raise ValueError(f"experiment {experiment_id} not found")
    return ResearchExperimentSchema.model_validate(row)


def update_research_experiment_status(
    tenant_id: int,
    experiment_id: int,
    request: ResearchExperimentStatusUpdateSchema,
    actor: str,
) -> ResearchExperimentSchema:
    rows = list_entities_for_tenant("research_experiments", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == experiment_id), None)
    if existing is None:
        raise ValueError(f"experiment {experiment_id} not found")
    updated = update_entity_for_tenant("research_experiments", experiment_id, {**existing, "status": request.status}, tenant_id)
    _emit_audit(
        actor=actor,
        action=build_audit_action("research", "experiment", "status_update"),
        path=f"/internal/research/experiments/{experiment_id}/status",
        metadata={"resource_id": str(experiment_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return ResearchExperimentSchema.model_validate(updated)


def get_research_health_snapshot(tenant_id: int) -> ResearchHealthSnapshotSchema:
    grants_rows = list_entities_for_tenant("research_grants", tenant_id)
    publication_rows = list_entities_for_tenant("research_publications", tenant_id)
    labs_rows = list_entities_for_tenant("research_labs", tenant_id)
    ip_rows = list_entities_for_tenant("research_ip_assets", tenant_id)
    experiment_rows = list_entities_for_tenant("research_experiments", tenant_id)

    today = date.today()
    near_deadline = 0
    grant_pipeline_at_risk = 0
    for row in grants_rows:
        status = str(row.get("status") or "")
        deadline = _parse_date(row.get("deadline"))
        days_left: int | None = None
        if deadline is not None:
            days_left = (deadline - today).days

        if status in {"active", "submitted"} and days_left is not None and 0 <= days_left <= 30:
            near_deadline += 1

        if status == "delayed":
            grant_pipeline_at_risk += 1
        elif status in {"active", "submitted"} and days_left is not None and days_left <= 45:
            grant_pipeline_at_risk += 1

    stalled_publications = 0
    publication_tracking_alerts = 0
    for row in publication_rows:
        status = str(row.get("status") or "")
        last_activity_days = _safe_int(row.get("last_activity_days"), default=0)
        if status == "stalled" or last_activity_days >= 90:
            stalled_publications += 1
        if status in {"submitted", "stalled"} and last_activity_days >= 60:
            publication_tracking_alerts += 1

    active_experiments = 0
    utilized_labs: set[str] = set()
    for row in experiment_rows:
        experiment_status = str(row.get("status") or "")
        if experiment_status in {"running", "paused"}:
            active_experiments += 1
            lab_code = str(row.get("lab_code") or "").strip()
            if lab_code:
                utilized_labs.add(lab_code)

    active_lab_codes: set[str] = set()
    for row in labs_rows:
        if str(row.get("status") or "") == "active":
            lab_code = str(row.get("lab_code") or "").strip()
            if lab_code:
                active_lab_codes.add(lab_code)

    labs_with_low_utilization = 0
    if active_lab_codes:
        labs_with_low_utilization = len(active_lab_codes - utilized_labs)
        labs_utilized = len(active_lab_codes & utilized_labs)
        lab_utilization_rate = (labs_utilized / len(active_lab_codes)) * 100
    else:
        lab_utilization_rate = 0.0

    return ResearchHealthSnapshotSchema(
        tenant_id=tenant_id,
        grants_total=len(grants_rows),
        grants_near_deadline=near_deadline,
        grant_pipeline_at_risk=grant_pipeline_at_risk,
        publications_total=len(publication_rows),
        stalled_publications=stalled_publications,
        publication_tracking_alerts=publication_tracking_alerts,
        labs_total=len(labs_rows),
        labs_with_low_utilization=labs_with_low_utilization,
        lab_utilization_rate=lab_utilization_rate,
        ip_assets_total=len(ip_rows),
        experiments_total=len(experiment_rows),
        active_experiments=active_experiments,
    )
