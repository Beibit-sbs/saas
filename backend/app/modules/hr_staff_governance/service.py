"""HR / Staff Governance service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.hr_staff_governance import models, repository
from app.modules.hr_staff_governance.dependencies import validate_tenant_id
from app.modules.hr_staff_governance.schemas import HRDashboardSummaryResponse, HRFoundationSummaryResponse, HRSafetyBoundaryResponse


EXPECTED_ROUTE_COUNT = models.EXPECTED_ROUTE_COUNT
EXPECTED_TABLE_COUNT = models.EXPECTED_TABLE_COUNT
EXPECTED_PERMISSION_COUNT = models.EXPECTED_PERMISSION_COUNT

REQUIRED_LIMITATIONS = [
	"metadata_only_foundation",
	"evidence_metadata_only",
	"human_review_required",
	"no_provider_live_integration",
	"no_payroll_execution",
	"no_automatic_decision",
	"no_external_db_sync",
]

ROLE_NAMES = [
	"HR_ADMIN",
	"HR_OFFICER",
	"HR_REVIEWER",
	"DEPARTMENT_HEAD",
	"FACULTY_ADMIN",
	"PAYROLL_COORDINATOR",
	"IAM_COORDINATOR",
	"DISCIPLINARY_COMMITTEE",
	"HIRING_COMMITTEE",
	"TRAINING_COORDINATOR",
	"LEAVE_MANAGER",
	"PROBATION_REVIEWER",
	"OFFBOARDING_COORDINATOR",
	"AUDIT_REVIEWER",
	"READ_ONLY_VIEWER",
]


def _now() -> datetime:
	return datetime.now(UTC)


def _validate_actor(actor_user_id: str | int | None) -> str:
	actor = str(actor_user_id or "").strip()
	if not actor:
		raise DomainValidationError("actor_user_id is required")
	return actor


def _commit(db: Session) -> None:
	try:
		db.commit()
	except Exception:
		db.rollback()
		raise


def _merge_limitations(values: list[str] | None) -> list[str]:
	merged = list(values or [])
	for item in REQUIRED_LIMITATIONS:
		if item not in merged:
			merged.append(item)
	return merged


def _base_create_payload(request, actor: str, *, status_default: str = "DRAFT", extra: dict[str, Any] | None = None) -> dict[str, Any]:
	payload = request.model_dump(exclude_none=True)
	payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
	payload["metadata_json"] = payload.pop("metadata", {})
	payload.setdefault("status", status_default)
	payload["human_review_required"] = True
	payload["fake_data"] = False
	payload["provider_connected"] = False
	payload["created_by_id"] = actor
	payload["updated_by_id"] = actor
	return payload | (extra or {})


def _base_update_payload(request, actor: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	payload = request.model_dump(exclude_none=True)
	if "limitations" in payload:
		payload["limitations_json"] = _merge_limitations(payload.pop("limitations"))
	if "metadata" in payload:
		payload["metadata_json"] = payload.pop("metadata")
	payload["human_review_required"] = True
	payload["fake_data"] = False
	payload["provider_connected"] = False
	payload["updated_by_id"] = actor
	return payload | (extra or {})


def _review_payload(request, actor: str, *, status_default: str | None = None) -> dict[str, Any]:
	if not request.reviewer_id:
		raise DomainValidationError("reviewer_id is required")
	payload = {
		"reviewer_id": request.reviewer_id,
		"decision": request.decision,
		"notes": request.notes,
		"metadata_json": dict(request.metadata),
		"limitations_json": _merge_limitations([]),
		"human_review_required": True,
		"fake_data": False,
		"provider_connected": False,
		"created_by_id": actor,
		"updated_by_id": actor,
	}
	if status_default is not None:
		payload["status"] = request.status or status_default
	return payload


def _audit(db: Session, tenant_id: int, *, source_entity_type: str, source_entity_id: int | None, event_type: str, actor_user_id: str, previous_status: str | None = None, new_status: str | None = None, payload: dict[str, Any] | None = None) -> None:
	repository.repo_create_audit_event(
		db,
		tenant_id,
		event_type=event_type,
		source_entity_type=source_entity_type,
		source_entity_id=source_entity_id,
		actor_user_id=actor_user_id,
		previous_status=previous_status,
		new_status=new_status,
		payload_json=payload or {},
		human_review_required=True,
		provider_connected=False,
		hidden_score_present=False,
	)


def _entity_id(entity: Any) -> int | None:
	value = getattr(entity, "id", None)
	return int(value) if isinstance(value, int) else value


def _entity_status(entity: Any) -> str | None:
	value = getattr(entity, "status", None)
	return str(value) if value is not None else None


def _entity_attr(entity: Any, name: str) -> Any:
	return getattr(entity, name, None)


def _foundation_summary(tenant_id: int) -> HRFoundationSummaryResponse:
	return HRFoundationSummaryResponse(
		tenant_id=tenant_id,
		module=models.MODULE_NAME,
		target_level=models.TARGET_LEVEL,
		foundation_status=models.FOUNDATION_STATUS,
		contract_version=models.CONTRACT_VERSION,
		source_spec_commit=models.SOURCE_SPEC_COMMIT,
		source_product_map_commit=models.SOURCE_PRODUCT_MAP_COMMIT,
		source_vertical_selection_commit=models.SOURCE_VERTICAL_SELECTION_COMMIT,
		product_vertical=models.PRODUCT_VERTICAL,
		capability_family_count=models.CAPABILITY_FAMILY_COUNT,
		detailed_capability_count=models.DETAILED_CAPABILITY_COUNT,
		workflow_group_count=models.WORKFLOW_GROUP_COUNT,
		role_count=models.ROLE_COUNT,
		runtime_mode=models.RUNTIME_MODE,
		data_source=models.DATA_SOURCE,
		table_count=models.EXPECTED_TABLE_COUNT,
		route_count=models.EXPECTED_ROUTE_COUNT,
		permission_count=models.EXPECTED_PERMISSION_COUNT,
	)


def get_hr_foundation_summary(db: Session, tenant_id: int) -> HRFoundationSummaryResponse:
	del db
	tenant_id = validate_tenant_id(tenant_id)
	return _foundation_summary(tenant_id)


def get_hr_safety_boundaries(db: Session, tenant_id: int) -> HRSafetyBoundaryResponse:
	del db
	tenant_id = validate_tenant_id(tenant_id)
	return HRSafetyBoundaryResponse(tenant_id=tenant_id)


def get_hr_dashboard_summary(db: Session, tenant_id: int) -> HRDashboardSummaryResponse:
	tenant_id = validate_tenant_id(tenant_id)
	summary = repository.repo_compute_dashboard_summary(db, tenant_id)
	limitations = list(dict.fromkeys(REQUIRED_LIMITATIONS))
	return HRDashboardSummaryResponse(
		tenant_id=tenant_id,
		generated_at=_now(),
		contract_version=models.CONTRACT_VERSION,
		source_spec_commit=models.SOURCE_SPEC_COMMIT,
		source_product_map_commit=models.SOURCE_PRODUCT_MAP_COMMIT,
		source_vertical_selection_commit=models.SOURCE_VERTICAL_SELECTION_COMMIT,
		runtime_mode=models.RUNTIME_MODE,
		data_source=models.DATA_SOURCE,
		fake_metrics=False,
		fake_hr_data=False,
		incomplete_data=True,
		human_review_required=True,
		provider_connected=False,
		live_provider_sync=False,
		payroll_execution_enabled=False,
		automatic_decision_enabled=False,
		hidden_score_present=False,
		limitation_flags=limitations,
		limitations=limitations,
		**summary,
	)


def list_hr_audit_events(db: Session, tenant_id: int):
	return repository.repo_list_audit_events(db, validate_tenant_id(tenant_id))


def list_hr_evidence_items(db: Session, tenant_id: int):
	return repository.repo_list_evidence_items(db, validate_tenant_id(tenant_id))


def create_staff_profile(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_staff_profile(db, tenant_id, **_base_create_payload(request, actor, status_default=models.StaffStatus.DRAFT))
	repository.repo_record_staff_status_history(db, tenant_id, staff_ref=_entity_attr(entity, "staff_ref"), previous_status=None, changed_by_id=actor, reason="created", source_reference=_entity_attr(entity, "source_reference"), evidence_status=_entity_attr(entity, "evidence_status"), human_review_required=True, fake_data=False, provider_connected=False, notes=_entity_attr(entity, "notes"), created_by_id=actor, updated_by_id=actor, metadata_json={}, limitations_json=_merge_limitations([]), status=_entity_status(entity))
	_audit(db, tenant_id, source_entity_type="staff_profile", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.STAFF_PROFILE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_staff_profile(db: Session, tenant_id: int, actor_user_id: str, staff_profile_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	current = repository.repo_get_staff_profile(db, tenant_id, staff_profile_id)
	if current is None:
		raise DomainValidationError(f"staff_profile {staff_profile_id} not found in tenant scope")
	entity = repository.repo_update_staff_profile(db, tenant_id, staff_profile_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="staff_profile", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.EMPLOYEE_RECORD_UPDATED, actor_user_id=actor, previous_status=getattr(current, "status", None), new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_employee_record(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_employee_record(db, tenant_id, **_base_create_payload(request, actor, status_default=models.StaffStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="employee_record", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.EMPLOYEE_RECORD_UPDATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_employee_record(db: Session, tenant_id: int, actor_user_id: str, employee_record_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_employee_record(db, tenant_id, employee_record_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="employee_record", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.EMPLOYEE_RECORD_UPDATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_recruitment_request(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_recruitment_request(db, tenant_id, **_base_create_payload(request, actor, status_default=models.RecruitmentStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="recruitment_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.RECRUITMENT_REQUEST_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_recruitment_request(db: Session, tenant_id: int, actor_user_id: str, recruitment_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_recruitment_request(db, tenant_id, recruitment_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="recruitment_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.RECRUITMENT_REQUEST_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_recruitment_request(db: Session, tenant_id: int, actor_user_id: str, recruitment_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_recruitment_request(db, tenant_id, recruitment_id, status=request.status or models.RecruitmentStatus.COMMITTEE_REVIEW, updated_by_id=actor, human_review_required=True, fake_data=False, provider_connected=False)
	review = repository.repo_create_hiring_committee_review(db, tenant_id, **_review_payload(request, actor, status_default=models.RecruitmentStatus.COMMITTEE_REVIEW), recruitment_ref=getattr(entity, "recruitment_ref", None), source_reference=getattr(entity, "source_reference", None), evidence_status=getattr(entity, "evidence_status", None))
	_audit(db, tenant_id, source_entity_type="recruitment_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.RECRUITMENT_REVIEW_RECORDED, actor_user_id=actor, new_status=request.status or models.RecruitmentStatus.COMMITTEE_REVIEW)
	_commit(db)
	return review


def create_onboarding_case(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_onboarding_case(db, tenant_id, **_base_create_payload(request, actor, status_default=models.OnboardingStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="onboarding_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.ONBOARDING_CASE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_onboarding_case(db: Session, tenant_id: int, actor_user_id: str, onboarding_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_onboarding_case(db, tenant_id, onboarding_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="onboarding_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.ONBOARDING_CHECKLIST_UPDATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_probation(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	review = repository.repo_record_probation_review(db, tenant_id, **_review_payload(request, actor, status_default=models.OnboardingStatus.REVIEW_REQUIRED), onboarding_ref=request.onboarding_ref)
	_audit(db, tenant_id, source_entity_type="probation_review", source_entity_id=_entity_id(review), event_type=models.AuditEventType.PROBATION_REVIEW_RECORDED, actor_user_id=actor, new_status=_entity_status(review))
	_commit(db)
	return review


def create_leave_request(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_leave_request(db, tenant_id, **_base_create_payload(request, actor, status_default=models.LeaveRequestStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="leave_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.LEAVE_REQUEST_SUBMITTED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_leave_request(db: Session, tenant_id: int, actor_user_id: str, leave_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_record_leave_review(db, tenant_id, leave_id, status=request.status or models.LeaveRequestStatus.HR_REVIEW, updated_by_id=actor, notes=request.notes, human_review_required=True, fake_data=False, provider_connected=False)
	_audit(db, tenant_id, source_entity_type="leave_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.LEAVE_REVIEW_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_appraisal_cycle(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_appraisal_cycle(db, tenant_id, **_base_create_payload(request, actor, status_default=models.AppraisalStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="appraisal_cycle", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.APPRAISAL_CYCLE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def record_appraisal_review(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	review = repository.repo_record_appraisal_review(db, tenant_id, **_review_payload(request, actor, status_default=models.AppraisalStatus.HUMAN_REVIEW_REQUIRED), appraisal_ref=request.appraisal_ref)
	_audit(db, tenant_id, source_entity_type="appraisal_review", source_entity_id=_entity_id(review), event_type=models.AuditEventType.APPRAISAL_REVIEW_RECORDED, actor_user_id=actor, new_status=_entity_status(review))
	_commit(db)
	return review


def create_training_certification(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_training_certification(db, tenant_id, **_base_create_payload(request, actor, status_default=models.TrainingStatus.PLANNED))
	_audit(db, tenant_id, source_entity_type="training_certification", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.TRAINING_CERTIFICATION_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_training_certification(db: Session, tenant_id: int, actor_user_id: str, training_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_training_certification(db, tenant_id, training_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="training_certification", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.CERTIFICATION_EXPIRY_FLAGGED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_staff_request(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_staff_request(db, tenant_id, **_base_create_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="staff_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.STAFF_REQUEST_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_staff_request(db: Session, tenant_id: int, actor_user_id: str, request_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_record_staff_request_review(db, tenant_id, request_id, status=request.status or models.RecruitmentStatus.UNDER_REVIEW, updated_by_id=actor, notes=request.notes, human_review_required=True, fake_data=False, provider_connected=False)
	_audit(db, tenant_id, source_entity_type="staff_request", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.STAFF_REQUEST_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_staff_appeal(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_staff_appeal(db, tenant_id, **_base_create_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="staff_appeal", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.STAFF_APPEAL_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_staff_appeal(db: Session, tenant_id: int, actor_user_id: str, appeal_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_record_staff_appeal_review(db, tenant_id, appeal_id, status=request.status or models.RecruitmentStatus.UNDER_REVIEW, updated_by_id=actor, notes=request.notes, human_review_required=True, fake_data=False, provider_connected=False)
	_audit(db, tenant_id, source_entity_type="staff_appeal", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.STAFF_APPEAL_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_policy_exception(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_policy_exception(db, tenant_id, **_base_create_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="policy_exception", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.POLICY_EXCEPTION_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def review_policy_exception(db: Session, tenant_id: int, actor_user_id: str, exception_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_record_policy_exception_review(db, tenant_id, exception_id, status=request.status or models.RecruitmentStatus.UNDER_REVIEW, updated_by_id=actor, notes=request.notes, human_review_required=True, fake_data=False, provider_connected=False)
	_audit(db, tenant_id, source_entity_type="policy_exception", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.POLICY_EXCEPTION_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_disciplinary_case(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_disciplinary_case(db, tenant_id, **_base_create_payload(request, actor, status_default=models.DisciplinaryCaseStatus.INTAKE))
	_audit(db, tenant_id, source_entity_type="disciplinary_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.DISCIPLINARY_CASE_INTAKE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def record_disciplinary_review(db: Session, tenant_id: int, actor_user_id: str, case_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	repository.repo_add_disciplinary_evidence(db, tenant_id, **_review_payload(request, actor, status_default=models.DisciplinaryCaseStatus.HUMAN_REVIEW_REQUIRED), case_ref=request.case_ref)
	entity = repository.repo_record_disciplinary_review(db, tenant_id, case_id, status=request.status or models.DisciplinaryCaseStatus.COMMITTEE_REVIEW, updated_by_id=actor, notes=request.notes, human_review_required=True, fake_data=False, provider_connected=False)
	_audit(db, tenant_id, source_entity_type="disciplinary_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.DISCIPLINARY_REVIEW_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_offboarding_case(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_offboarding_case(db, tenant_id, **_base_create_payload(request, actor, status_default=models.OffboardingStatus.DRAFT))
	_audit(db, tenant_id, source_entity_type="offboarding_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.OFFBOARDING_CASE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def update_offboarding_case(db: Session, tenant_id: int, actor_user_id: str, offboarding_id: int, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_update_offboarding_case(db, tenant_id, offboarding_id, **_base_update_payload(request, actor))
	_audit(db, tenant_id, source_entity_type="offboarding_case", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.OFFBOARDING_CASE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def record_access_lifecycle_review(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	review = repository.repo_record_access_lifecycle_review(db, tenant_id, **_review_payload(request, actor, status_default=models.OffboardingStatus.ACCESS_REVIEW_REQUIRED), offboarding_ref=request.offboarding_ref)
	_audit(db, tenant_id, source_entity_type="access_lifecycle_review", source_entity_id=_entity_id(review), event_type=models.AuditEventType.ACCESS_REVIEW_RECORDED, actor_user_id=actor, new_status=_entity_status(review))
	_commit(db)
	return review


def create_workload_bridge_record(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_workload_bridge_record(db, tenant_id, **_base_create_payload(request, actor, extra={"read_only_first": True, "mutation_allowed": False}))
	_audit(db, tenant_id, source_entity_type="workload_bridge_record", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.WORKLOAD_BRIDGE_RECORD_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def create_payroll_readiness_profile(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_payroll_readiness_profile(db, tenant_id, **_base_create_payload(request, actor, status_default=models.ProviderReadinessStatus.NOT_CONFIGURED, extra={"payroll_execution_enabled": False, "live_provider_sync": False, "provider_name": request.provider_name or "HR_PAYROLL_PROVIDER"}))
	_audit(db, tenant_id, source_entity_type="payroll_readiness_profile", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.PAYROLL_READINESS_PROFILE_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def record_provider_readiness_evidence(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_record_provider_readiness_evidence(db, tenant_id, **_base_create_payload(request, actor, status_default=models.ProviderReadinessStatus.NOT_CONFIGURED, extra={"provider_name": request.provider_name, "readiness_status": models.ProviderReadinessStatus.NOT_CONFIGURED, "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "live_integration_deferred": True}))
	_audit(db, tenant_id, source_entity_type="provider_readiness_evidence", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.PROVIDER_READINESS_EVIDENCE_RECORDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def list_staff_profiles(db: Session, tenant_id: int):
	return repository.repo_list_staff_profiles(db, validate_tenant_id(tenant_id))


def get_staff_profile(db: Session, tenant_id: int, staff_profile_id: int):
	tenant_id = validate_tenant_id(tenant_id)
	entity = repository.repo_get_staff_profile(db, tenant_id, staff_profile_id)
	if entity is None:
		raise DomainValidationError(f"staff_profile {staff_profile_id} not found in tenant scope")
	return entity


def list_employee_records(db: Session, tenant_id: int):
	return repository.repo_list_employee_records(db, validate_tenant_id(tenant_id))


def list_faculty_profiles(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.FacultyProfile, validate_tenant_id(tenant_id))


def list_recruitment_requests(db: Session, tenant_id: int):
	return repository.repo_list_recruitment_requests(db, validate_tenant_id(tenant_id))


def create_hiring_evidence_pack(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_create_hiring_evidence_pack(
		db,
		tenant_id,
		**_base_create_payload(
			request,
			actor,
			status_default=models.RecruitmentStatus.EVIDENCE_COMPLETE,
			extra={
				"evidence_pack_ref": request.recruitment_ref or f"hiring-evidence-{int(_now().timestamp())}",
				"recruitment_ref": request.recruitment_ref,
				"reference_uri": request.source_reference,
			},
		),
	)
	_audit(db, tenant_id, source_entity_type="hiring_evidence_pack", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.HIRING_EVIDENCE_PACK_CREATED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def list_hiring_evidence_packs(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.HiringEvidencePack, validate_tenant_id(tenant_id))


def list_onboarding_cases(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.OnboardingCase, validate_tenant_id(tenant_id))


def list_probation_reviews(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.ProbationReview, validate_tenant_id(tenant_id))


def list_leave_requests(db: Session, tenant_id: int):
	return repository.repo_list_leave_requests(db, validate_tenant_id(tenant_id))


def list_attendance_metadata(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.StaffAttendanceMetadata, validate_tenant_id(tenant_id))


def list_appraisals(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.PerformanceAppraisalCycle, validate_tenant_id(tenant_id))


def list_appraisal_reviews(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.AppraisalReviewEvidence, validate_tenant_id(tenant_id))


def list_training_certifications(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.TrainingCertification, validate_tenant_id(tenant_id))


def list_staff_requests(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.StaffRequest, validate_tenant_id(tenant_id))


def list_staff_appeals(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.StaffAppeal, validate_tenant_id(tenant_id))


def list_policy_exceptions(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.PolicyException, validate_tenant_id(tenant_id))


def list_disciplinary_cases(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.DisciplinaryCase, validate_tenant_id(tenant_id))


def create_disciplinary_evidence(db: Session, tenant_id: int, actor_user_id: str, request):
	tenant_id = validate_tenant_id(tenant_id)
	actor = _validate_actor(actor_user_id)
	entity = repository.repo_add_disciplinary_evidence(
		db,
		tenant_id,
		**_review_payload(request, actor, status_default=models.DisciplinaryCaseStatus.HUMAN_REVIEW_REQUIRED),
		case_ref=request.case_ref,
		review_ref=request.case_ref or f"disciplinary-evidence-{int(_now().timestamp())}",
	)
	_audit(db, tenant_id, source_entity_type="disciplinary_evidence", source_entity_id=_entity_id(entity), event_type=models.AuditEventType.DISCIPLINARY_EVIDENCE_ADDED, actor_user_id=actor, new_status=_entity_status(entity))
	_commit(db)
	return entity


def list_disciplinary_evidence(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.DisciplinaryReviewEvidence, validate_tenant_id(tenant_id))


def list_offboarding_cases(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.ExitOffboardingCase, validate_tenant_id(tenant_id))


def list_access_lifecycle_reviews(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.AccessLifecycleReview, validate_tenant_id(tenant_id))


def list_workload_bridge_records(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.WorkloadBridgeRecord, validate_tenant_id(tenant_id))


def list_payroll_readiness_profiles(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.PayrollReadinessProfile, validate_tenant_id(tenant_id))


def list_provider_readiness_evidence(db: Session, tenant_id: int):
	return repository._tenant_filtered_list(db, models.ProviderReadinessEvidence, validate_tenant_id(tenant_id))


def list_limitations(db: Session, tenant_id: int) -> list[dict[str, Any]]:
	limitations: list[dict[str, Any]] = []
	for item in repository.repo_list_evidence_items(db, validate_tenant_id(tenant_id)):
		for code in list(getattr(item, "limitations", []) or []):
			limitations.append({"code": code, "text": code, "source_entity_type": item.source_entity_type, "source_entity_id": item.source_entity_id, "metadata": dict(getattr(item, "metadata_json", {}) or {})})
	for code in REQUIRED_LIMITATIONS:
		limitations.append({"code": code, "text": code, "source_entity_type": None, "source_entity_id": None, "metadata": {}})
	seen: set[tuple[str, str | None, int | None]] = set()
	deduped: list[dict[str, Any]] = []
	for item in limitations:
		key = (item["code"], item["source_entity_type"], item["source_entity_id"])
		if key not in seen:
			deduped.append(item)
			seen.add(key)
	return deduped


def get_health_summary(db: Session, tenant_id: int) -> dict[str, Any]:
	summary = repository.repo_compute_dashboard_summary(db, validate_tenant_id(tenant_id))
	total_records = sum(sum(group.values()) for group in summary.values())
	return {
		"tenant_id": tenant_id,
		"module": models.MODULE_NAME,
		"target_level": models.TARGET_LEVEL,
		"foundation_status": models.FOUNDATION_STATUS,
		"contract_version": models.CONTRACT_VERSION,
		"runtime_mode": models.RUNTIME_MODE,
		"table_count": models.EXPECTED_TABLE_COUNT,
		"route_count": models.EXPECTED_ROUTE_COUNT,
		"permission_count": models.EXPECTED_PERMISSION_COUNT,
		"total_records": total_records,
		"fake_metrics": False,
		"fake_hr_data": False,
		"provider_connected": False,
		"live_provider_sync": False,
		"payroll_execution_enabled": False,
		"automatic_decision_enabled": False,
		"hidden_score_present": False,
		"human_review_required": True,
		"limitations": REQUIRED_LIMITATIONS,
	}


def get_bridge_summary(db: Session, tenant_id: int, bridge_name: str) -> dict[str, Any]:
	tenant_id = validate_tenant_id(tenant_id)
	bridge_items = list_workload_bridge_records(db, tenant_id)
	matching = [item for item in bridge_items if getattr(item, "bridge_target", None) == bridge_name]
	return {
		"tenant_id": tenant_id,
		"bridge": bridge_name,
		"read_only_first": True,
		"mutation_allowed": False,
		"records": len(matching),
		"provider_connected": False,
	}


def get_brain_signals_summary(db: Session, tenant_id: int) -> dict[str, Any]:
	del db
	tenant_id = validate_tenant_id(tenant_id)
	return {
		"tenant_id": tenant_id,
		"mode": "GOVERNANCE_ONLY",
		"human_review_required": True,
		"safe_draft_only": True,
		"signals": [
			"faculty_overload_signal",
			"staff_compliance_risk_signal",
			"training_expiry_signal",
			"probation_review_signal",
			"access_lifecycle_gap_signal",
			"payroll_data_quality_signal",
			"HR_policy_exception_signal",
		],
		"safe_drafts": [
			"safe_staff_case_summary_draft",
			"safe_training_compliance_summary_draft",
			"safe_hr_policy_exception_draft",
		],
	}


def get_metadata_contract(db: Session, tenant_id: int) -> dict[str, Any]:
	del db
	return _foundation_summary(validate_tenant_id(tenant_id)).model_dump()


def get_readiness_summary(db: Session, tenant_id: int) -> dict[str, Any]:
	del db
	tenant_id = validate_tenant_id(tenant_id)
	return {
		"tenant_id": tenant_id,
		"providers": [
			{"provider": "ONE_C_KZ", "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "provider_connected": False, "live_integration_deferred": True},
			{"provider": "HR_PAYROLL_PROVIDER", "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "provider_connected": False, "live_integration_deferred": True},
			{"provider": "IDP_SSO_KZ", "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "provider_connected": False, "live_integration_deferred": True},
			{"provider": "EDS_KZ", "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "provider_connected": False, "live_integration_deferred": True},
			{"provider": "EGOV_LABOR_REGISTRY", "credentials_present": False, "live_call_count": 0, "sync_count": 0, "external_submission_count": 0, "provider_connected": False, "live_integration_deferred": True},
		],
	}