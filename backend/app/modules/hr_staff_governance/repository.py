"""HR / Staff Governance repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError
from app.modules.hr_staff_governance import models


def _now() -> datetime:
	return datetime.now(UTC)


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
	if resource is None:
		raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
	return resource


def _tenant_filtered_get(db: Session, model, tenant_id: int, resource_id: int):
	return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def _tenant_filtered_list(db: Session, model, tenant_id: int):
	order_column = getattr(model, "created_at", None)
	query = select(model).where(model.tenant_id == tenant_id)
	if order_column is not None:
		query = query.order_by(order_column.desc())
	return list(db.execute(query).scalars().all())


def _create(db: Session, model, tenant_id: int, **kwargs):
	obj = model(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
	db.add(obj)
	db.flush()
	db.refresh(obj)
	return obj


def _update(db: Session, resource, **kwargs):
	for key, value in kwargs.items():
		setattr(resource, key, value)
	if hasattr(resource, "updated_at"):
		resource.updated_at = _now()
	db.flush()
	db.refresh(resource)
	return resource


def _count_by_status(db: Session, model, tenant_id: int) -> dict[str, int]:
	rows = db.execute(select(model.status, func.count()).where(model.tenant_id == tenant_id).group_by(model.status)).all()
	return {str(status): int(total) for status, total in rows}


def _count_by_field(db: Session, model, tenant_id: int, field_name: str) -> dict[str, int]:
	field = getattr(model, field_name)
	rows = db.execute(select(field, func.count()).where(model.tenant_id == tenant_id).group_by(field)).all()
	return {str(key): int(total) for key, total in rows}


def repo_get_foundation_summary(db: Session, tenant_id: int) -> dict[str, int]:
	del db
	return {
		"tenant_id": tenant_id,
		"table_count": models.EXPECTED_TABLE_COUNT,
		"route_count": models.EXPECTED_ROUTE_COUNT,
		"permission_count": models.EXPECTED_PERMISSION_COUNT,
	}


def repo_compute_dashboard_summary(db: Session, tenant_id: int) -> dict[str, dict[str, int]]:
	return {
		"staff_lifecycle_summary": _count_by_status(db, models.StaffProfile, tenant_id),
		"recruitment_readiness": _count_by_status(db, models.RecruitmentRequest, tenant_id),
		"onboarding_progress": _count_by_status(db, models.OnboardingCase, tenant_id),
		"employee_record_completeness": _count_by_status(db, models.EmployeeRecord, tenant_id),
		"leave_request_review_status": _count_by_status(db, models.LeaveRequest, tenant_id),
		"training_certification_risk": _count_by_status(db, models.TrainingCertification, tenant_id),
		"disciplinary_human_review_queue": _count_by_status(db, models.DisciplinaryCase, tenant_id),
		"offboarding_access_review": _count_by_status(db, models.ExitOffboardingCase, tenant_id),
		"workload_bridge_visibility": _count_by_field(db, models.WorkloadBridgeRecord, tenant_id, "bridge_target"),
		"payroll_readiness_profile": _count_by_status(db, models.PayrollReadinessProfile, tenant_id),
		"provider_readiness_status": _count_by_field(db, models.ProviderReadinessEvidence, tenant_id, "readiness_status"),
	}


def repo_list_audit_events(db: Session, tenant_id: int) -> list[models.AuditEvent]:
	return list(db.execute(select(models.AuditEvent).where(models.AuditEvent.tenant_id == tenant_id).order_by(models.AuditEvent.created_at.desc())).scalars().all())


def repo_list_evidence_items(db: Session, tenant_id: int) -> list[models.EvidenceRepository]:
	return list(db.execute(select(models.EvidenceRepository).where(models.EvidenceRepository.tenant_id == tenant_id).order_by(models.EvidenceRepository.created_at.desc())).scalars().all())


def repo_create_staff_profile(db: Session, tenant_id: int, **kwargs) -> models.StaffProfile:
	return _create(db, models.StaffProfile, tenant_id, **kwargs)


def repo_get_staff_profile(db: Session, tenant_id: int, staff_profile_id: int) -> models.StaffProfile | None:
	return _tenant_filtered_get(db, models.StaffProfile, tenant_id, staff_profile_id)


def repo_list_staff_profiles(db: Session, tenant_id: int) -> list[models.StaffProfile]:
	return _tenant_filtered_list(db, models.StaffProfile, tenant_id)


def repo_update_staff_profile(db: Session, tenant_id: int, staff_profile_id: int, **kwargs) -> models.StaffProfile:
	return _update(db, _require(repo_get_staff_profile(db, tenant_id, staff_profile_id), tenant_id, "staff_profile", staff_profile_id), **kwargs)


def repo_create_employee_record(db: Session, tenant_id: int, **kwargs) -> models.EmployeeRecord:
	return _create(db, models.EmployeeRecord, tenant_id, **kwargs)


def repo_update_employee_record(db: Session, tenant_id: int, employee_record_id: int, **kwargs) -> models.EmployeeRecord:
	return _update(db, _require(_tenant_filtered_get(db, models.EmployeeRecord, tenant_id, employee_record_id), tenant_id, "employee_record", employee_record_id), **kwargs)


def repo_list_employee_records(db: Session, tenant_id: int) -> list[models.EmployeeRecord]:
	return _tenant_filtered_list(db, models.EmployeeRecord, tenant_id)


def repo_record_staff_status_history(db: Session, tenant_id: int, **kwargs) -> models.StaffStatusHistory:
	return _create(db, models.StaffStatusHistory, tenant_id, **kwargs)


def repo_create_recruitment_request(db: Session, tenant_id: int, **kwargs) -> models.RecruitmentRequest:
	return _create(db, models.RecruitmentRequest, tenant_id, **kwargs)


def repo_update_recruitment_request(db: Session, tenant_id: int, recruitment_id: int, **kwargs) -> models.RecruitmentRequest:
	return _update(db, _require(_tenant_filtered_get(db, models.RecruitmentRequest, tenant_id, recruitment_id), tenant_id, "recruitment_request", recruitment_id), **kwargs)


def repo_list_recruitment_requests(db: Session, tenant_id: int) -> list[models.RecruitmentRequest]:
	return _tenant_filtered_list(db, models.RecruitmentRequest, tenant_id)


def repo_create_hiring_committee_review(db: Session, tenant_id: int, **kwargs) -> models.HiringCommitteeReview:
	return _create(db, models.HiringCommitteeReview, tenant_id, **kwargs)


def repo_create_hiring_evidence_pack(db: Session, tenant_id: int, **kwargs) -> models.HiringEvidencePack:
	return _create(db, models.HiringEvidencePack, tenant_id, **kwargs)


def repo_create_onboarding_case(db: Session, tenant_id: int, **kwargs) -> models.OnboardingCase:
	return _create(db, models.OnboardingCase, tenant_id, **kwargs)


def repo_update_onboarding_case(db: Session, tenant_id: int, onboarding_id: int, **kwargs) -> models.OnboardingCase:
	return _update(db, _require(_tenant_filtered_get(db, models.OnboardingCase, tenant_id, onboarding_id), tenant_id, "onboarding_case", onboarding_id), **kwargs)


def repo_create_onboarding_checklist_item(db: Session, tenant_id: int, **kwargs) -> models.OnboardingChecklistItem:
	return _create(db, models.OnboardingChecklistItem, tenant_id, **kwargs)


def repo_record_probation_review(db: Session, tenant_id: int, **kwargs) -> models.ProbationReview:
	return _create(db, models.ProbationReview, tenant_id, **kwargs)


def repo_create_leave_request(db: Session, tenant_id: int, **kwargs) -> models.LeaveRequest:
	return _create(db, models.LeaveRequest, tenant_id, **kwargs)


def repo_record_leave_review(db: Session, tenant_id: int, leave_id: int, **kwargs) -> models.LeaveRequest:
	return _update(db, _require(_tenant_filtered_get(db, models.LeaveRequest, tenant_id, leave_id), tenant_id, "leave_request", leave_id), **kwargs)


def repo_list_leave_requests(db: Session, tenant_id: int) -> list[models.LeaveRequest]:
	return _tenant_filtered_list(db, models.LeaveRequest, tenant_id)


def repo_create_staff_request(db: Session, tenant_id: int, **kwargs) -> models.StaffRequest:
	return _create(db, models.StaffRequest, tenant_id, **kwargs)


def repo_record_staff_request_review(db: Session, tenant_id: int, request_id: int, **kwargs) -> models.StaffRequest:
	return _update(db, _require(_tenant_filtered_get(db, models.StaffRequest, tenant_id, request_id), tenant_id, "staff_request", request_id), **kwargs)


def repo_create_staff_appeal(db: Session, tenant_id: int, **kwargs) -> models.StaffAppeal:
	return _create(db, models.StaffAppeal, tenant_id, **kwargs)


def repo_record_staff_appeal_review(db: Session, tenant_id: int, appeal_id: int, **kwargs) -> models.StaffAppeal:
	return _update(db, _require(_tenant_filtered_get(db, models.StaffAppeal, tenant_id, appeal_id), tenant_id, "staff_appeal", appeal_id), **kwargs)


def repo_create_policy_exception(db: Session, tenant_id: int, **kwargs) -> models.PolicyException:
	return _create(db, models.PolicyException, tenant_id, **kwargs)


def repo_record_policy_exception_review(db: Session, tenant_id: int, exception_id: int, **kwargs) -> models.PolicyException:
	return _update(db, _require(_tenant_filtered_get(db, models.PolicyException, tenant_id, exception_id), tenant_id, "policy_exception", exception_id), **kwargs)


def repo_create_appraisal_cycle(db: Session, tenant_id: int, **kwargs) -> models.PerformanceAppraisalCycle:
	return _create(db, models.PerformanceAppraisalCycle, tenant_id, **kwargs)


def repo_record_appraisal_review(db: Session, tenant_id: int, **kwargs) -> models.AppraisalReviewEvidence:
	return _create(db, models.AppraisalReviewEvidence, tenant_id, **kwargs)


def repo_create_training_certification(db: Session, tenant_id: int, **kwargs) -> models.TrainingCertification:
	return _create(db, models.TrainingCertification, tenant_id, **kwargs)


def repo_update_training_certification(db: Session, tenant_id: int, training_id: int, **kwargs) -> models.TrainingCertification:
	return _update(db, _require(_tenant_filtered_get(db, models.TrainingCertification, tenant_id, training_id), tenant_id, "training_certification", training_id), **kwargs)


def repo_create_disciplinary_case(db: Session, tenant_id: int, **kwargs) -> models.DisciplinaryCase:
	return _create(db, models.DisciplinaryCase, tenant_id, **kwargs)


def repo_add_disciplinary_evidence(db: Session, tenant_id: int, **kwargs) -> models.DisciplinaryReviewEvidence:
	return _create(db, models.DisciplinaryReviewEvidence, tenant_id, **kwargs)


def repo_record_disciplinary_review(db: Session, tenant_id: int, case_id: int, **kwargs) -> models.DisciplinaryCase:
	return _update(db, _require(_tenant_filtered_get(db, models.DisciplinaryCase, tenant_id, case_id), tenant_id, "disciplinary_case", case_id), **kwargs)


def repo_create_offboarding_case(db: Session, tenant_id: int, **kwargs) -> models.ExitOffboardingCase:
	return _create(db, models.ExitOffboardingCase, tenant_id, **kwargs)


def repo_update_offboarding_case(db: Session, tenant_id: int, offboarding_id: int, **kwargs) -> models.ExitOffboardingCase:
	return _update(db, _require(_tenant_filtered_get(db, models.ExitOffboardingCase, tenant_id, offboarding_id), tenant_id, "offboarding_case", offboarding_id), **kwargs)


def repo_record_access_lifecycle_review(db: Session, tenant_id: int, **kwargs) -> models.AccessLifecycleReview:
	return _create(db, models.AccessLifecycleReview, tenant_id, **kwargs)


def repo_create_workload_bridge_record(db: Session, tenant_id: int, **kwargs) -> models.WorkloadBridgeRecord:
	return _create(db, models.WorkloadBridgeRecord, tenant_id, **kwargs)


def repo_create_payroll_readiness_profile(db: Session, tenant_id: int, **kwargs) -> models.PayrollReadinessProfile:
	return _create(db, models.PayrollReadinessProfile, tenant_id, **kwargs)


def repo_record_provider_readiness_evidence(db: Session, tenant_id: int, **kwargs) -> models.ProviderReadinessEvidence:
	return _create(db, models.ProviderReadinessEvidence, tenant_id, **kwargs)


def repo_create_audit_event(db: Session, tenant_id: int, **kwargs) -> models.AuditEvent:
	obj = models.AuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
	db.add(obj)
	db.flush()
	db.refresh(obj)
	return obj


def repo_create_evidence_record(db: Session, tenant_id: int, **kwargs) -> models.EvidenceRepository:
	obj = models.EvidenceRepository(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
	db.add(obj)
	db.flush()
	db.refresh(obj)
	return obj


def repo_record_limitation_flag(db: Session, tenant_id: int, *, code: str, text: str, source_entity_type: str | None = None, source_entity_id: int | None = None, actor_user_id: str | None = None, metadata_json: dict | None = None) -> models.EvidenceRepository:
	return repo_create_evidence_record(
		db,
		tenant_id,
		status="METADATA_ONLY",
		source_entity_type=source_entity_type or "limitation_flag",
		source_entity_id=source_entity_id,
		evidence_type="limitation_flag",
		title=text,
		source_reference=code,
		evidence_status="LIMITATION",
		human_review_required=True,
		fake_data=False,
		provider_connected=False,
		created_by_id=actor_user_id,
		updated_by_id=actor_user_id,
		limitations=[code],
		metadata_json=metadata_json or {},
	)