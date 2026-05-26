"""FastAPI router for HR / Staff Governance backend foundation."""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import integrity_error_to_http, permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, OptimisticLockConflictError, TenantResourceNotFoundError
from app.modules.hr_staff_governance import permissions, service
from app.modules.hr_staff_governance.dependencies import get_hr_staff_governance_db, require_hr_staff_governance_tenant
from app.modules.hr_staff_governance.schemas import (
	HRAccessLifecycleReviewCreate,
	HRAppraisalCycleCreate,
	HRAppraisalReviewCreate,
	HRAppraisalResponse,
	HRAuditEventResponse,
	HRDashboardSummaryResponse,
	HRDisciplinaryCaseCreate,
	HRDisciplinaryCaseResponse,
	HRDisciplinaryReviewCreate,
	HREmployeeRecordCreate,
	HREmployeeRecordResponse,
	HREmployeeRecordUpdate,
	HREvidenceResponse,
	HRFoundationSummaryResponse,
	HRHiringCommitteeReviewCreate,
	HRHiringCommitteeReviewResponse,
	HRLeaveRequestCreate,
	HRLeaveRequestResponse,
	HRLeaveReviewCreate,
	HRLimitationResponse,
	HRMetadataResponseBase,
	HROffboardingCaseCreate,
	HROffboardingCaseResponse,
	HROnboardingCaseCreate,
	HROnboardingCaseResponse,
	HROnboardingCaseUpdate,
	HRPayrollReadinessProfileCreate,
	HRPayrollReadinessResponse,
	HRPolicyExceptionCreate,
	HRPolicyExceptionResponse,
	HRProbationReviewCreate,
	HRProbationReviewResponse,
	HRProviderReadinessResponse,
	HRRecruitmentRequestCreate,
	HRRecruitmentRequestResponse,
	HRRecruitmentRequestUpdate,
	HRSafetyBoundaryResponse,
	HRStaffAppealCreate,
	HRStaffAppealResponse,
	HRStaffProfileCreate,
	HRStaffProfileResponse,
	HRStaffProfileUpdate,
	HRStaffRequestCreate,
	HRStaffRequestResponse,
	HRTrainingCertificationCreate,
	HRTrainingCertificationResponse,
	HRWorkloadBridgeRecordCreate,
	HRWorkloadBridgeRecordResponse,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/hr-staff-governance", tags=["hr-staff-governance"])

_Tenant = Annotated[int, Depends(require_hr_staff_governance_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_hr_staff_governance_db)]


class ErrorDetailResponse(BaseModel):
	detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
	try:
		return schema_cls.model_validate(payload)
	except ValidationError as exc:
		raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
	if isinstance(exc, PermissionError):
		raise permission_error_to_http(exc)
	if isinstance(exc, TenantResourceNotFoundError):
		raise tenant_not_found_to_http(exc)
	if isinstance(exc, (DomainValidationError, ValueError)):
		raise validation_error_to_http(exc)
	if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
		raise integrity_error_to_http(exc)
	raise exc


def _resp(obj: Any, schema_cls):
	if isinstance(obj, dict):
		data = dict(obj)
	else:
		data = obj.__dict__.copy()
	if "limitations_json" in data:
		data["limitations"] = list(data.pop("limitations_json") or [])
	if "limitations" in data and data["limitations"] is None:
		data["limitations"] = []
	if "metadata_json" in data:
		data["metadata"] = dict(data.pop("metadata_json") or {})
	if "summary_json" in data:
		data["summary"] = dict(data.pop("summary_json") or {})
	if "payload_json" in data:
		data["payload"] = dict(data.pop("payload_json") or {})
	return schema_cls.model_validate(data)


def _register_collection_routes(
	path: str,
	*,
	list_service: Callable[[Session, int], list[Any]],
	list_schema,
	read_permission: str,
	create_service: Callable[..., Any] | None = None,
	create_schema: type[BaseModel] | None = None,
	create_response_schema=None,
	create_permission: str | None = None,
	update_service: Callable[..., Any] | None = None,
	update_schema: type[BaseModel] | None = None,
	update_response_schema=None,
	update_permission: str | None = None,
	review_service: Callable[..., Any] | None = None,
	review_schema: type[BaseModel] | None = None,
	review_response_schema=None,
	review_permission: str | None = None,
):
	def list_endpoint(
		actor: str = Depends(get_actor),
		permission_check: None = Depends(permission_dependency(read_permission)),
		tenant: int = Depends(require_hr_staff_governance_tenant),
		db: Session = Depends(get_hr_staff_governance_db),
	):
		try:
			del actor, permission_check
			return [_resp(item, list_schema) for item in list_service(db, tenant)]
		except Exception as exc:
			_handle(exc)

	list_endpoint.__name__ = f"list_{path.strip('/').replace('/', '_').replace('-', '_')}"
	router.add_api_route(path, list_endpoint, methods=["GET"], response_model=list[list_schema])

	if create_service is not None and create_schema is not None and create_permission is not None and create_response_schema is not None:
		def create_endpoint(
			payload: dict[str, Any] = Body(...),
			actor: str = Depends(get_actor),
			permission_check: None = Depends(permission_dependency(create_permission)),
			tenant: int = Depends(require_hr_staff_governance_tenant),
			db: Session = Depends(get_hr_staff_governance_db),
		):
			try:
				del permission_check
				body = _parse_payload(create_schema, payload)
				return _resp(create_service(db, tenant, actor, body), create_response_schema)
			except Exception as exc:
				_handle(exc)

		create_endpoint.__name__ = f"create_{path.strip('/').replace('/', '_').replace('-', '_')}"
		router.add_api_route(path, create_endpoint, methods=["POST"], response_model=create_response_schema, status_code=201)

	if update_service is not None and update_schema is not None and update_permission is not None and update_response_schema is not None:
		def update_endpoint(
			resource_id: int,
			payload: dict[str, Any] = Body(...),
			actor: str = Depends(get_actor),
			permission_check: None = Depends(permission_dependency(update_permission)),
			tenant: int = Depends(require_hr_staff_governance_tenant),
			db: Session = Depends(get_hr_staff_governance_db),
		):
			try:
				del permission_check
				body = _parse_payload(update_schema, payload)
				return _resp(update_service(db, tenant, actor, resource_id, body), update_response_schema)
			except Exception as exc:
				_handle(exc)

		update_endpoint.__name__ = f"update_{path.strip('/').replace('/', '_').replace('-', '_')}"
		router.add_api_route(f"{path}/{{resource_id}}", update_endpoint, methods=["PATCH"], response_model=update_response_schema)

	if review_service is not None and review_schema is not None and review_permission is not None and review_response_schema is not None:
		def review_endpoint(
			resource_id: int,
			payload: dict[str, Any] = Body(...),
			actor: str = Depends(get_actor),
			permission_check: None = Depends(permission_dependency(review_permission)),
			tenant: int = Depends(require_hr_staff_governance_tenant),
			db: Session = Depends(get_hr_staff_governance_db),
		):
			try:
				del permission_check
				body = _parse_payload(review_schema, payload)
				return _resp(review_service(db, tenant, actor, resource_id, body), review_response_schema)
			except Exception as exc:
				_handle(exc)

		review_endpoint.__name__ = f"review_{path.strip('/').replace('/', '_').replace('-', '_')}"
		router.add_api_route(f"{path}/{{resource_id}}/review", review_endpoint, methods=["POST"], response_model=review_response_schema, status_code=201)


@router.get("/health", response_model=dict[str, Any])
def get_health(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.HEALTH_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
	try:
		del actor, _
		return service.get_health_summary(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/overview", response_model=HRFoundationSummaryResponse)
def get_overview(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))], tenant: _Tenant, db: _DB) -> HRFoundationSummaryResponse:
	try:
		del actor, _
		return service.get_hr_foundation_summary(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/dashboard", response_model=HRDashboardSummaryResponse)
def get_dashboard(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))], tenant: _Tenant, db: _DB) -> HRDashboardSummaryResponse:
	try:
		del actor, _
		return service.get_hr_dashboard_summary(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/safety-boundaries", response_model=HRSafetyBoundaryResponse)
def get_safety_boundaries(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.LIMITATIONS_READ))], tenant: _Tenant, db: _DB) -> HRSafetyBoundaryResponse:
	try:
		del actor, _
		return service.get_hr_safety_boundaries(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/readiness", response_model=dict[str, Any])
def get_readiness(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROVIDER_READINESS_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
	try:
		del actor, _
		return service.get_readiness_summary(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/brain-signals", response_model=dict[str, Any])
def get_brain_signals(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.WORKLOAD_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
	try:
		del actor, _
		return service.get_brain_signals_summary(db, tenant)
	except Exception as exc:
		_handle(exc)


@router.get("/workload-bridge/{bridge_name}/summary", response_model=dict[str, Any])
def get_bridge_summary(bridge_name: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.WORKLOAD_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
	try:
		del actor, _
		return service.get_bridge_summary(db, tenant, bridge_name)
	except Exception as exc:
		_handle(exc)


_register_collection_routes(
	"/staff-profiles",
	list_service=service.list_staff_profiles,
	list_schema=HRStaffProfileResponse,
	read_permission=permissions.STAFF_PROFILES_READ,
	create_service=service.create_staff_profile,
	create_schema=HRStaffProfileCreate,
	create_response_schema=HRStaffProfileResponse,
	create_permission=permissions.STAFF_PROFILES_CREATE,
	update_service=service.update_staff_profile,
	update_schema=HRStaffProfileUpdate,
	update_response_schema=HRStaffProfileResponse,
	update_permission=permissions.STAFF_PROFILES_UPDATE,
)
_register_collection_routes(
	"/employee-records",
	list_service=service.list_employee_records,
	list_schema=HREmployeeRecordResponse,
	read_permission=permissions.EMPLOYEE_RECORDS_READ,
	create_service=service.create_employee_record,
	create_schema=HREmployeeRecordCreate,
	create_response_schema=HREmployeeRecordResponse,
	create_permission=permissions.EMPLOYEE_RECORDS_CREATE,
	update_service=service.update_employee_record,
	update_schema=HREmployeeRecordUpdate,
	update_response_schema=HREmployeeRecordResponse,
	update_permission=permissions.EMPLOYEE_RECORDS_UPDATE,
)
_register_collection_routes(
	"/faculty-profiles",
	list_service=service.list_faculty_profiles,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.FACULTY_PROFILES_READ,
)
_register_collection_routes(
	"/recruitment-requests",
	list_service=service.list_recruitment_requests,
	list_schema=HRRecruitmentRequestResponse,
	read_permission=permissions.RECRUITMENT_READ,
	create_service=service.create_recruitment_request,
	create_schema=HRRecruitmentRequestCreate,
	create_response_schema=HRRecruitmentRequestResponse,
	create_permission=permissions.RECRUITMENT_CREATE,
	update_service=service.update_recruitment_request,
	update_schema=HRRecruitmentRequestUpdate,
	update_response_schema=HRRecruitmentRequestResponse,
	update_permission=permissions.RECRUITMENT_REVIEW,
	review_service=service.review_recruitment_request,
	review_schema=HRHiringCommitteeReviewCreate,
	review_response_schema=HRHiringCommitteeReviewResponse,
	review_permission=permissions.RECRUITMENT_REVIEW,
)
_register_collection_routes(
	"/hiring-evidence",
	list_service=service.list_hiring_evidence_packs,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.HIRING_EVIDENCE_READ,
	create_service=service.create_hiring_evidence_pack,
	create_schema=HRRecruitmentRequestCreate,
	create_response_schema=HRMetadataResponseBase,
	create_permission=permissions.HIRING_EVIDENCE_CREATE,
)
_register_collection_routes(
	"/onboarding-cases",
	list_service=service.list_onboarding_cases,
	list_schema=HROnboardingCaseResponse,
	read_permission=permissions.ONBOARDING_READ,
	create_service=service.create_onboarding_case,
	create_schema=HROnboardingCaseCreate,
	create_response_schema=HROnboardingCaseResponse,
	create_permission=permissions.ONBOARDING_CREATE,
	update_service=service.update_onboarding_case,
	update_schema=HROnboardingCaseUpdate,
	update_response_schema=HROnboardingCaseResponse,
	update_permission=permissions.ONBOARDING_UPDATE,
)
_register_collection_routes(
	"/probation-reviews",
	list_service=service.list_probation_reviews,
	list_schema=HRProbationReviewResponse,
	read_permission=permissions.PROBATION_READ,
	create_service=service.review_probation,
	create_schema=HRProbationReviewCreate,
	create_response_schema=HRProbationReviewResponse,
	create_permission=permissions.PROBATION_REVIEW,
)
_register_collection_routes(
	"/leave-requests",
	list_service=service.list_leave_requests,
	list_schema=HRLeaveRequestResponse,
	read_permission=permissions.LEAVE_READ,
	create_service=service.create_leave_request,
	create_schema=HRLeaveRequestCreate,
	create_response_schema=HRLeaveRequestResponse,
	create_permission=permissions.LEAVE_CREATE,
	review_service=service.review_leave_request,
	review_schema=HRLeaveReviewCreate,
	review_response_schema=HRLeaveRequestResponse,
	review_permission=permissions.LEAVE_REVIEW,
)
_register_collection_routes(
	"/attendance",
	list_service=service.list_attendance_metadata,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.ATTENDANCE_READ,
)
_register_collection_routes(
	"/staff-requests",
	list_service=service.list_staff_requests,
	list_schema=HRStaffRequestResponse,
	read_permission=permissions.STAFF_REQUESTS_READ,
	create_service=service.create_staff_request,
	create_schema=HRStaffRequestCreate,
	create_response_schema=HRStaffRequestResponse,
	create_permission=permissions.STAFF_REQUESTS_CREATE,
	review_service=service.review_staff_request,
	review_schema=HRLeaveReviewCreate,
	review_response_schema=HRStaffRequestResponse,
	review_permission=permissions.STAFF_REQUESTS_REVIEW,
)
_register_collection_routes(
	"/staff-appeals",
	list_service=service.list_staff_appeals,
	list_schema=HRStaffAppealResponse,
	read_permission=permissions.STAFF_APPEALS_READ,
	create_service=service.create_staff_appeal,
	create_schema=HRStaffAppealCreate,
	create_response_schema=HRStaffAppealResponse,
	create_permission=permissions.STAFF_APPEALS_CREATE,
	review_service=service.review_staff_appeal,
	review_schema=HRLeaveReviewCreate,
	review_response_schema=HRStaffAppealResponse,
	review_permission=permissions.STAFF_APPEALS_REVIEW,
)
_register_collection_routes(
	"/policy-exceptions",
	list_service=service.list_policy_exceptions,
	list_schema=HRPolicyExceptionResponse,
	read_permission=permissions.POLICY_EXCEPTIONS_READ,
	create_service=service.create_policy_exception,
	create_schema=HRPolicyExceptionCreate,
	create_response_schema=HRPolicyExceptionResponse,
	create_permission=permissions.POLICY_EXCEPTIONS_CREATE,
	review_service=service.review_policy_exception,
	review_schema=HRLeaveReviewCreate,
	review_response_schema=HRPolicyExceptionResponse,
	review_permission=permissions.POLICY_EXCEPTIONS_REVIEW,
)
_register_collection_routes(
	"/appraisals",
	list_service=service.list_appraisals,
	list_schema=HRAppraisalResponse,
	read_permission=permissions.APPRAISALS_READ,
	create_service=service.create_appraisal_cycle,
	create_schema=HRAppraisalCycleCreate,
	create_response_schema=HRAppraisalResponse,
	create_permission=permissions.APPRAISALS_CREATE,
)
_register_collection_routes(
	"/appraisal-reviews",
	list_service=service.list_appraisal_reviews,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.APPRAISALS_READ,
	create_service=service.record_appraisal_review,
	create_schema=HRAppraisalReviewCreate,
	create_response_schema=HRMetadataResponseBase,
	create_permission=permissions.APPRAISALS_REVIEW,
)
_register_collection_routes(
	"/training-certifications",
	list_service=service.list_training_certifications,
	list_schema=HRTrainingCertificationResponse,
	read_permission=permissions.TRAINING_READ,
	create_service=service.create_training_certification,
	create_schema=HRTrainingCertificationCreate,
	create_response_schema=HRTrainingCertificationResponse,
	create_permission=permissions.TRAINING_CREATE,
	update_service=service.update_training_certification,
	update_schema=HRTrainingCertificationCreate,
	update_response_schema=HRTrainingCertificationResponse,
	update_permission=permissions.TRAINING_UPDATE,
)
_register_collection_routes(
	"/disciplinary-cases",
	list_service=service.list_disciplinary_cases,
	list_schema=HRDisciplinaryCaseResponse,
	read_permission=permissions.DISCIPLINARY_CASES_READ,
	create_service=service.create_disciplinary_case,
	create_schema=HRDisciplinaryCaseCreate,
	create_response_schema=HRDisciplinaryCaseResponse,
	create_permission=permissions.DISCIPLINARY_CASES_CREATE,
	review_service=service.record_disciplinary_review,
	review_schema=HRDisciplinaryReviewCreate,
	review_response_schema=HRDisciplinaryCaseResponse,
	review_permission=permissions.DISCIPLINARY_CASES_REVIEW,
)
_register_collection_routes(
	"/disciplinary-evidence",
	list_service=service.list_disciplinary_evidence,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.DISCIPLINARY_EVIDENCE_READ,
	create_service=service.create_disciplinary_evidence,
	create_schema=HRDisciplinaryReviewCreate,
	create_response_schema=HRMetadataResponseBase,
	create_permission=permissions.DISCIPLINARY_EVIDENCE_CREATE,
)
_register_collection_routes(
	"/offboarding-cases",
	list_service=service.list_offboarding_cases,
	list_schema=HROffboardingCaseResponse,
	read_permission=permissions.OFFBOARDING_READ,
	create_service=service.create_offboarding_case,
	create_schema=HROffboardingCaseCreate,
	create_response_schema=HROffboardingCaseResponse,
	create_permission=permissions.OFFBOARDING_CREATE,
	update_service=service.update_offboarding_case,
	update_schema=HROffboardingCaseCreate,
	update_response_schema=HROffboardingCaseResponse,
	update_permission=permissions.OFFBOARDING_UPDATE,
)
_register_collection_routes(
	"/access-lifecycle-reviews",
	list_service=service.list_access_lifecycle_reviews,
	list_schema=HRMetadataResponseBase,
	read_permission=permissions.ACCESS_LIFECYCLE_READ,
	create_service=service.record_access_lifecycle_review,
	create_schema=HRAccessLifecycleReviewCreate,
	create_response_schema=HRMetadataResponseBase,
	create_permission=permissions.ACCESS_LIFECYCLE_REVIEW,
)
_register_collection_routes(
	"/workload-bridge-records",
	list_service=service.list_workload_bridge_records,
	list_schema=HRWorkloadBridgeRecordResponse,
	read_permission=permissions.WORKLOAD_BRIDGE_READ,
	create_service=service.create_workload_bridge_record,
	create_schema=HRWorkloadBridgeRecordCreate,
	create_response_schema=HRWorkloadBridgeRecordResponse,
	create_permission=permissions.WORKLOAD_BRIDGE_READ,
)
_register_collection_routes(
	"/payroll-readiness-profiles",
	list_service=service.list_payroll_readiness_profiles,
	list_schema=HRPayrollReadinessResponse,
	read_permission=permissions.PAYROLL_READINESS_READ,
	create_service=service.create_payroll_readiness_profile,
	create_schema=HRPayrollReadinessProfileCreate,
	create_response_schema=HRPayrollReadinessResponse,
	create_permission=permissions.PAYROLL_READINESS_REVIEW,
)
_register_collection_routes(
	"/provider-readiness-evidence",
	list_service=service.list_provider_readiness_evidence,
	list_schema=HRProviderReadinessResponse,
	read_permission=permissions.PROVIDER_READINESS_READ,
)


@router.get("/audit", response_model=list[HRAuditEventResponse])
def list_audit_events(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))], tenant: _Tenant, db: _DB) -> list[HRAuditEventResponse]:
	try:
		del actor, _
		return [_resp(item, HRAuditEventResponse) for item in service.list_hr_audit_events(db, tenant)]
	except Exception as exc:
		_handle(exc)


@router.get("/limitations", response_model=list[HRLimitationResponse])
def list_limitations(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.LIMITATIONS_READ))], tenant: _Tenant, db: _DB) -> list[HRLimitationResponse]:
	try:
		del actor, _
		return [_resp(item, HRLimitationResponse) for item in service.list_limitations(db, tenant)]
	except Exception as exc:
		_handle(exc)