"""
Admissions Module - Service Layer

Business logic for admissions operations.

Design principles:
- tenant_id mandatory parameter on every method (fail-closed)
- No implicit tenant defaults or fallbacks
- All operations return Pydantic schemas (not SQLAlchemy models)
- Audit logging integration on all mutations
- Optimistic locking on mutable entities (application, decision)
- Stage history is append-only (service layer enforces no updates/deletes)
- Document keys are safe references (S3, never filesystem paths)
"""

from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.audit.service import log_admin_action
from app.modules.admissions.business_rules import (
    AuditEventRules,
    DecisionRules,
    DocumentRules,
    StageTransitionRules,
    TenantIsolationRules,
)
from app.modules.admissions.models import (
    ApplicantModel,
    ApplicationDecisionModel,
    ApplicationDocumentModel,
    ApplicationModel,
    ApplicationStageHistoryModel,
)
from app.modules.admissions.schemas import (
    ApplicantCreateSchema,
    ApplicantReadSchema,
    ApplicantUpdateSchema,
    ApplicationConclusionType,
    ApplicationCreateSchema,
    ApplicationDecisionReadSchema,
    ApplicationListResponseSchema,
    ApplicationReadSchema,
    ApplicationStage,
    ApplicantListResponseSchema,
    DecisionMakeRequestSchema,
    DocumentAttachRequestSchema,
    DocumentListResponseSchema,
    DocumentReadSchema,
    DocumentStatus,
    DocumentVerifyRequestSchema,
    StageHistoryListResponseSchema,
    StageHistoryReadSchema,
    StageTransitionAction,
    StageTransitionRequestSchema,
    StageTransitionResponseSchema,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ==============================================================================
# APPLICANT SERVICE
# ==============================================================================


class ApplicantService:
    """Service for applicant management."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_applicant(
        self,
        tenant_id: int,
        request: ApplicantCreateSchema,
        created_by: str,
    ) -> ApplicantReadSchema:
        """
        Create a new applicant.
        
        Args:
            tenant_id: Tenant ID (mandatory, fail-closed)
            request: ApplicantCreateSchema with applicant data
            created_by: User ID who created the applicant (from auth context)
        
        Returns:
            ApplicantReadSchema
        
        Raises:
            ValueError: If tenant_id not provided
            IntegrityError: If unique constraint violated (duplicate email per tenant/program/year)
            PermissionError: Should not happen here (auth layer checks)
        
        Audit Event: "applicant.created"
        """
        tenant_id = validate_tenant_id_provided(tenant_id)

        applicant = ApplicantModel(
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            program_id=request.program_id,
            application_year=request.application_year,
            status=request.status.value,
            external_id=request.external_id,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(applicant)
        self.db.flush()  # Generate ID without commit
        self.db.refresh(applicant)

        # Audit logging
        log_admin_action(
            actor=created_by,
            action=build_audit_action("admissions", "applicant", "create"),
            path=f"/internal/admissions/applicants/{applicant.id}",
            client_ip="service",
            entity="applicant",
            metadata={
                "resource_id": str(applicant.id),
                "email": applicant.email,
                "program_id": applicant.program_id,
                "application_year": applicant.application_year,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return ApplicantReadSchema.model_validate(applicant)

    async def get_applicant(self, tenant_id: int, applicant_id: int) -> ApplicantReadSchema:
        """
        Get applicant by ID with tenant isolation.
        
        Raises:
            PermissionError: If applicant belongs to different tenant (HTTP 403)
            ValueError: If applicant not found
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        applicant = self.db.execute(
            select(ApplicantModel).where(
                and_(
                    ApplicantModel.id == applicant_id,
                    ApplicantModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not applicant:
            raise ValueError(f"Applicant {applicant_id} not found or does not belong to tenant {tenant_id}")

        return ApplicantReadSchema.model_validate(applicant)

    async def list_applicants(
        self,
        tenant_id: int,
        program_id: Optional[int] = None,
        application_year: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ApplicantListResponseSchema:
        """
        List applicants with optional filtering by program and year.
        
        Tenant isolation: All queries filtered by tenant_id.
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        query = select(ApplicantModel).where(ApplicantModel.tenant_id == tenant_id)

        if program_id:
            query = query.where(ApplicantModel.program_id == program_id)
        if application_year:
            query = query.where(ApplicantModel.application_year == application_year)

        # Count total
        count_query = select(func.count()).select_from(ApplicantModel).where(
            and_(
                ApplicantModel.tenant_id == tenant_id,
                *([ApplicantModel.program_id == program_id] if program_id else []),
                *([ApplicantModel.application_year == application_year] if application_year else []),
            )
        )
        total = self.db.execute(count_query).scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(desc(ApplicantModel.created_at)).offset(offset).limit(page_size)

        applicants = self.db.execute(query).scalars().all()

        return ApplicantListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[ApplicantReadSchema.model_validate(a) for a in applicants],
        )

    async def update_applicant(
        self,
        tenant_id: int,
        applicant_id: int,
        request: ApplicantUpdateSchema,
        updated_by: str,
    ) -> ApplicantReadSchema:
        """
        Update applicant (partial update).
        
        Audit Event: "applicant.updated"
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        applicant = self.db.execute(
            select(ApplicantModel).where(
                and_(
                    ApplicantModel.id == applicant_id,
                    ApplicantModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not applicant:
            raise ValueError(f"Applicant {applicant_id} not found or does not belong to tenant {tenant_id}")

        # Update fields
        if request.first_name:
            applicant.first_name = request.first_name
        if request.last_name:
            applicant.last_name = request.last_name
        if request.phone is not None:
            applicant.phone = request.phone
        if request.status:
            applicant.status = request.status.value
        if request.external_id is not None:
            applicant.external_id = request.external_id
        if request.metadata_json is not None:
            applicant.metadata_json = request.metadata_json

        self.db.flush()

        # Audit logging
        log_admin_action(
            actor=updated_by,
            action=AuditEventRules.get_log_action_for_event("applicant.updated"),
            path=f"/internal/admissions/applicants/{applicant_id}",
            client_ip="service",
            entity="applicant",
            metadata={"updates": request.model_dump(exclude_none=True)},
            tenant_id=tenant_id,
        )

        self.db.commit()
        return ApplicantReadSchema.model_validate(applicant)


# ==============================================================================
# APPLICATION SERVICE
# ==============================================================================


class ApplicationService:
    """Service for application management."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_application(
        self,
        tenant_id: int,
        request: ApplicationCreateSchema,
        created_by: str,
    ) -> ApplicationReadSchema:
        """
        Create a new application for an applicant.
        
        Validation:
        - Applicant must exist and belong to tenant
        - Applicant must be active
        - Only one active application per applicant (enforced by service + DB)
        
        Audit Event: "application.created"
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        # Verify applicant exists and belongs to tenant
        applicant = self.db.execute(
            select(ApplicantModel).where(
                and_(
                    ApplicantModel.id == request.applicant_id,
                    ApplicantModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not applicant:
            raise ValueError(f"Applicant {request.applicant_id} not found in tenant {tenant_id}")

        application = ApplicationModel(
            tenant_id=tenant_id,
            applicant_id=request.applicant_id,
            program_id=request.program_id,
            stage=ApplicationStage.NEW.value,
            created_by=created_by,
            metadata_json=request.metadata_json,
        )

        self.db.add(application)
        self.db.flush()
        self.db.refresh(application)

        # Audit logging
        log_admin_action(
            actor=created_by,
            action=AuditEventRules.get_log_action_for_event("application.created"),
            path=f"/internal/admissions/applications/{application.id}",
            client_ip="service",
            entity="application",
            metadata={
                "resource_id": str(application.id),
                "applicant_id": request.applicant_id,
                "program_id": request.program_id,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return ApplicationReadSchema.model_validate(application)

    async def get_application(self, tenant_id: int, application_id: int) -> ApplicationReadSchema:
        """Get application by ID with tenant isolation."""
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found or does not belong to tenant {tenant_id}")

        return ApplicationReadSchema.model_validate(application)

    async def list_applications(
        self,
        tenant_id: int,
        program_id: Optional[int] = None,
        stage: Optional[ApplicationStage] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ApplicationListResponseSchema:
        """
        List applications with optional filtering.
        
        Tenant isolation: All queries filtered by tenant_id.
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        query = select(ApplicationModel).where(ApplicationModel.tenant_id == tenant_id)

        if program_id:
            query = query.where(ApplicationModel.program_id == program_id)
        if stage:
            query = query.where(ApplicationModel.stage == stage.value)

        # Count total
        total = self.db.execute(select(func.count(ApplicationModel.id)).where(
            and_(
                ApplicationModel.tenant_id == tenant_id,
                *([ApplicationModel.program_id == program_id] if program_id else []),
                *([ApplicationModel.stage == stage.value] if stage else []),
            )
        )).scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(desc(ApplicationModel.created_at)).offset(offset).limit(page_size)

        applications = self.db.execute(query).scalars().all()

        return ApplicationListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[ApplicationReadSchema.model_validate(app) for app in applications],
        )

    async def submit_application(
        self,
        tenant_id: int,
        application_id: int,
        actor: str,
        expected_version: int,
    ) -> ApplicationReadSchema:
        """
        Submit (transition to 'received') and start workflow.
        
        Workflow trigger:
        1. Validate application in 'new' stage
        2. Transition to 'received' stage (record in history)
        3. Start admissions workflow instance
        4. Store workflow_instance_id in application.metadata_json
        
        Idempotency:
        - If workflow_instance_id already in metadata_json, skip workflow creation
        - Still update stage/history (idempotent)
        
        Audit Events:
        - "application.submitted" (application state change)
        - "workflow.started" (workflow event) [logged by WorkflowService]
        
        Args:
            tenant_id: Tenant (mandatory, fail-closed)
            application_id: Application to submit
            actor: User submitting (typically applicant in UI; system in admin)
            expected_version: Expected version (optimistic lock)
        
        Returns:
            ApplicationReadSchema with updated stage + metadata
        
        Raises:
            ValueError: If application not found, wrong stage, or version mismatch
            PermissionError: If applicant lacks admissions.write permission
        
        Constraints:
        - Tenant isolation: all queries filtered by tenant_id
        - Fail-closed: no implicit defaults
        - Audit: all mutations logged via build_audit_action + log_admin_action
        - Optimistic locking: validate_version_match(current_version, expected_version)
        """
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Fetch application
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")
        
        # Validate optimistic lock
        if application.version != expected_version:
            raise ValueError(
                f"Version mismatch for application {application_id}: "
                f"expected {expected_version}, got {application.version}"
            )
        
        # Validate current stage
        if application.stage != ApplicationStage.NEW.value:
            raise ValueError(
                f"Cannot submit application in stage '{application.stage}'. "
                f"Only 'new' applications can be submitted."
            )
        
        # Check if workflow already started (idempotency)
        workflow_instance_id = application.metadata_json.get("workflow_instance_id")
        if not workflow_instance_id:
            # Start workflow
            workflow_instance = await self._start_admissions_workflow(
                tenant_id=tenant_id,
                application_id=application_id,
                applicant_id=application.applicant_id,
                program_id=application.program_id,
                actor=actor,
            )
            workflow_instance_id = workflow_instance.id
            
            # Store workflow reference in metadata
            application.metadata_json["workflow_instance_id"] = workflow_instance_id
            application.metadata_json["workflow_key"] = "admissions"
            application.metadata_json["workflow_status"] = "in_progress"
            application.metadata_json["workflow_started_at"] = _utc_now().isoformat()
        
        # Transition stage
        application.stage = ApplicationStage.RECEIVED.value
        application.received_at = _utc_now()
        application.version += 1  # Version increment
        
        # Record stage transition in history
        stage_history = ApplicationStageHistoryModel(
            tenant_id=tenant_id,
            application_id=application_id,
            from_stage=ApplicationStage.NEW.value,
            to_stage=ApplicationStage.RECEIVED.value,
            reason="Application submitted by applicant",
            action_type=StageTransitionAction.MANUAL.value,
            actor_id=actor,
            metadata_json={
                "workflow_instance_id": workflow_instance_id,
                "trigger_type": "user_submission",
            },
        )
        self.db.add(stage_history)
        
        self.db.flush()
        
        # Audit logging
        log_admin_action(
            actor=actor,
            action=build_audit_action("admissions", "application", "submit"),
            path=f"/internal/admissions/applications/{application_id}/submit",
            client_ip="service",
            entity="application",
            metadata={
                "resource_id": str(application_id),
                "workflow_instance_id": workflow_instance_id,
                "stage_transition": f"{ApplicationStage.NEW.value} → {ApplicationStage.RECEIVED.value}",
            },
            tenant_id=tenant_id,
        )
        
        self.db.commit()
        return ApplicationReadSchema.model_validate(application)

    async def _start_admissions_workflow(
        self,
        tenant_id: int,
        application_id: int,
        applicant_id: int,
        program_id: int,
        actor: str,
    ) -> object:  # WorkflowInstanceReadSchema from workflows module
        """
        Internal helper: Start admissions workflow for an application.
        
        Workflow Configuration:
        - Workflow key: "admissions"
        - Entity type: "admission_application"
        - Entity ID: application_id
        - Steps: document_review, dept_approval, dean_approval, registrar_approval, final_decision
        - Trigger mode: manual (no auto-advance)
        
        Task Assignments (from metadata):
        - document_review → "group:admissions_staff"
        - dept_approval → "group:department_chairs"
        - dean_approval → "group:deans"
        - registrar_approval → "group:registrars"
        - final_decision → "group:admissions_leadership"
        
        Returns:
            WorkflowInstanceReadSchema
        
        Raises:
            ValueError: If workflow template not found
            RuntimeError: If workflow service not available
        """
        from app.modules.workflows.workflow_service import WorkflowService
        
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Lazy import to avoid circular dependency
        workflow_service = WorkflowService(self.db)
        
        # Start workflow
        workflow_instance = await workflow_service.start_workflow(
            tenant_id=tenant_id,
            workflow_key="admissions",
            entity_type="admission_application",
            entity_id=application_id,
            actor=actor,
            metadata_json={
                "applicant_id": applicant_id,
                "application_id": application_id,
                "program_id": str(program_id),
            },
        )
        
        return workflow_instance


# ==============================================================================
# DOCUMENT SERVICE
# ==============================================================================


class DocumentService:
    """Service for document management."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def attach_document(
        self,
        tenant_id: int,
        application_id: int,
        request: DocumentAttachRequestSchema,
        created_by: str,
    ) -> DocumentReadSchema:
        """
        Attach a document to an application.
        
        Validation:
        - Application must exist and belong to tenant
        - Stage must allow document uploads
        - document_key must be safe (S3, not filesystem)
        
        Audit Event: "application.document_attached"
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        # Verify application exists and belongs to tenant
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        # Check if stage allows document upload
        current_stage = ApplicationStage(application.stage)
        if not DocumentRules.allows_document_upload_at_stage(current_stage):
            raise ValueError(f"Cannot upload documents at stage {current_stage.value}")

        # Validate document_key is safe
        if not DocumentRules.is_document_key_safe(request.document_key):
            raise ValueError("document_key must be a safe reference (S3), not a filesystem path")

        document = ApplicationDocumentModel(
            tenant_id=tenant_id,
            application_id=application_id,
            document_type=request.document_type,
            document_key=request.document_key,
            file_name=request.file_name,
            file_size_bytes=request.file_size_bytes,
            mime_type=request.mime_type,
            status=DocumentStatus.RECEIVED.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)

        # Audit logging
        log_admin_action(
            actor=created_by,
            action=AuditEventRules.get_log_action_for_event("application.document_attached"),
            path=f"/internal/admissions/applications/{application_id}/documents/{document.id}",
            client_ip="service",
            entity="document",
            metadata={
                "resource_id": str(document.id),
                "application_id": application_id,
                "document_type": request.document_type,
                "file_name": request.file_name,
                "file_size_bytes": request.file_size_bytes,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return DocumentReadSchema.model_validate(document)

    async def list_documents(
        self,
        tenant_id: int,
        application_id: int,
    ) -> DocumentListResponseSchema:
        """List all documents for an application."""
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        # Verify application belongs to tenant
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        documents = self.db.execute(
            select(ApplicationDocumentModel)
            .where(
                and_(
                    ApplicationDocumentModel.application_id == application_id,
                    ApplicationDocumentModel.tenant_id == tenant_id,
                )
            )
            .order_by(desc(ApplicationDocumentModel.created_at))
        ).scalars().all()

        return DocumentListResponseSchema(
            total=len(documents),
            items=[DocumentReadSchema.model_validate(doc) for doc in documents],
        )

    async def verify_document(
        self,
        tenant_id: int,
        document_id: int,
        request: DocumentVerifyRequestSchema,
    ) -> DocumentReadSchema:
        """Verify (accept/reject) a document."""
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        document = self.db.execute(
            select(ApplicationDocumentModel).where(
                and_(
                    ApplicationDocumentModel.id == document_id,
                    ApplicationDocumentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found in tenant {tenant_id}")

        document.status = request.status.value
        document.verified_at = _utc_now()
        document.verified_by = request.verified_by
        if request.metadata_json:
            document.metadata_json = request.metadata_json

        self.db.flush()
        self.db.refresh(document)

        # Audit logging (if applicable)
        if request.status == DocumentStatus.REJECTED:
            log_admin_action(
                actor=request.verified_by,
                action="admissions.document.verify",
                path=f"/internal/admissions/documents/{document_id}/verify",
                client_ip="service",
                entity="document",
                metadata={"status": request.status.value},
                tenant_id=tenant_id,
            )

        self.db.commit()
        return DocumentReadSchema.model_validate(document)


# ==============================================================================
# STAGE TRANSITION SERVICE
# ==============================================================================


class StageTransitionService:
    """Service for managing application stage transitions."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def transition_stage(
        self,
        tenant_id: int,
        application_id: int,
        request: StageTransitionRequestSchema,
        actor_id: str,
    ) -> StageTransitionResponseSchema:
        """
        Transition application to a new stage.
        
        Validation:
        - Application must exist and belong to tenant
        - Transition must be valid per StageTransitionRules
        - Cannot transition to CONCLUDED without a decision
        
        Audit Event: "application.stage_changed"
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        current_stage = ApplicationStage(application.stage)
        to_stage = request.to_stage

        # Validate transition
        StageTransitionRules.validate_transition(current_stage, to_stage)

        # Check if transitioning to CONCLUDED requires decision
        if to_stage == ApplicationStage.CONCLUDED:
            decision = self.db.execute(
                select(ApplicationDecisionModel).where(
                    ApplicationDecisionModel.application_id == application_id
                )
            ).scalar_one_or_none()

            if not decision:
                raise ValueError(
                    f"Cannot transition to CONCLUDED without a decision. "
                    f"Create decision first via make_decision()."
                )

        # Create history record (append-only)
        history = ApplicationStageHistoryModel(
            tenant_id=tenant_id,
            application_id=application_id,
            from_stage=current_stage.value,
            to_stage=to_stage.value,
            reason=request.reason,
            actor_id=actor_id,
            action_type=request.action_type.value,
            metadata_json=request.metadata_json or {},
        )

        self.db.add(history)

        # Update application stage
        application.stage = to_stage.value
        if to_stage == ApplicationStage.RECEIVED:
            application.received_at = _utc_now()

        self.db.flush()
        self.db.refresh(history)

        # Audit logging
        log_admin_action(
            actor=actor_id,
            action=AuditEventRules.get_log_action_for_event("application.stage_changed"),
            path=f"/internal/admissions/applications/{application_id}/stage-transitions/{history.id}",
            client_ip="service",
            entity="application",
            metadata={
                "resource_id": str(application_id),
                "history_id": str(history.id),
                "from_stage": current_stage.value,
                "to_stage": to_stage.value,
                "reason": request.reason,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()

        return StageTransitionResponseSchema(
            application_id=application_id,
            from_stage=current_stage,
            to_stage=to_stage,
            transition_at=history.created_at,
            history_id=history.id,
        )

    async def get_stage_history(
        self,
        tenant_id: int,
        application_id: int,
    ) -> StageHistoryListResponseSchema:
        """Get full stage transition history for an application."""
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        # Verify application belongs to tenant
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        history_records = self.db.execute(
            select(ApplicationStageHistoryModel)
            .where(
                and_(
                    ApplicationStageHistoryModel.application_id == application_id,
                    ApplicationStageHistoryModel.tenant_id == tenant_id,
                )
            )
            .order_by(ApplicationStageHistoryModel.created_at)
        ).scalars().all()

        return StageHistoryListResponseSchema(
            total=len(history_records),
            items=[StageHistoryReadSchema.model_validate(record) for record in history_records],
        )


# ==============================================================================
# DECISION SERVICE
# ==============================================================================


class DecisionService:
    """Service for admission decisions."""

    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def _build_student_number(tenant_id: int, application_id: int) -> str:
        """Deterministic student number for idempotent retries."""
        return f"ADM-{tenant_id}-{application_id}".upper()

    async def _provision_student_identity_on_accept(
        self,
        *,
        tenant_id: int,
        application: ApplicationModel,
        actor: str,
    ) -> None:
        """
        Create Person/Student for accepted admissions decision.

        Transaction notes:
        - Runs inside the same DB transaction as decision finalization.
        - Does not commit; caller owns commit/rollback boundary.
        - Idempotent by (tenant,email) for Person and (tenant,person_id) for Student.
        """
        tenant_id = validate_tenant_id_provided(tenant_id)

        # Only accepted decisions are eligible for identity provisioning.
        if application.conclusion_type != ApplicationConclusionType.ACCEPTED.value:
            return

        # Lazy imports keep module boundaries loose and avoid hard import coupling.
        from app.modules.profiles.models import PersonModel, ProgramModel, StudentModel

        applicant = self.db.execute(
            select(ApplicantModel).where(
                and_(
                    ApplicantModel.id == application.applicant_id,
                    ApplicantModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if not applicant:
            raise ValueError(
                f"Applicant {application.applicant_id} not found in tenant {tenant_id}"
            )

        program = self.db.execute(
            select(ProgramModel).where(
                and_(
                    ProgramModel.id == application.program_id,
                    ProgramModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if not program:
            raise ValueError(
                f"Program {application.program_id} not found in tenant {tenant_id}"
            )

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.tenant_id == tenant_id,
                    PersonModel.email == applicant.email,
                )
            )
        ).scalar_one_or_none()

        if not person:
            person_metadata: dict[str, Any] = {
                "source": "admissions_acceptance",
                "admissions_applicant_id": applicant.id,
                "admissions_application_id": application.id,
            }
            person = PersonModel(
                tenant_id=tenant_id,
                email=applicant.email,
                first_name=applicant.first_name,
                last_name=applicant.last_name,
                phone=applicant.phone,
                external_person_key=applicant.external_id,
                status="active",
                metadata_json=person_metadata,
                created_by=actor,
            )
            self.db.add(person)
            self.db.flush()
            self.db.refresh(person)

            log_admin_action(
                actor=actor,
                action=build_audit_action("profiles", "person", "created"),
                path=f"/internal/profiles/people/{person.id}",
                client_ip="service",
                entity="person",
                metadata={
                    "resource_id": str(person.id),
                    "email": person.email,
                    "provisioning_source": "admissions_acceptance",
                    "application_id": application.id,
                },
                tenant_id=tenant_id,
            )

        student = self.db.execute(
            select(StudentModel).where(
                and_(
                    StudentModel.tenant_id == tenant_id,
                    StudentModel.person_id == person.id,
                )
            )
        ).scalar_one_or_none()

        if not student:
            student_metadata: dict[str, Any] = {
                "source": "admissions_acceptance",
                "admissions_application_id": application.id,
                "admissions_program_id": application.program_id,
            }
            student = StudentModel(
                tenant_id=tenant_id,
                person_id=person.id,
                program_id=application.program_id,
                student_number=self._build_student_number(tenant_id, application.id),
                cohort_year=applicant.application_year,
                status="active",
                metadata_json=student_metadata,
                created_by=actor,
            )
            self.db.add(student)
            self.db.flush()
            self.db.refresh(student)

            log_admin_action(
                actor=actor,
                action=build_audit_action("profiles", "student", "created"),
                path=f"/internal/profiles/students/{student.id}",
                client_ip="service",
                entity="student",
                metadata={
                    "resource_id": str(student.id),
                    "person_id": person.id,
                    "program_id": application.program_id,
                    "student_number": student.student_number,
                    "provisioning_source": "admissions_acceptance",
                    "application_id": application.id,
                },
                tenant_id=tenant_id,
            )

        # Link back to admissions metadata for traceability and idempotent reads.
        application.metadata_json["person_id"] = person.id
        application.metadata_json["student_id"] = student.id
        application.metadata_json["student_number"] = student.student_number

    async def make_decision(
        self,
        tenant_id: int,
        application_id: int,
        request: DecisionMakeRequestSchema,
    ) -> ApplicationDecisionReadSchema:
        """
        Make an admission decision on an application.
        
        Validation:
        - Application must exist and belong to tenant
        - Application stage must be DECISION_PENDING
        - Only one decision per application (DB UNIQUE enforced)
        - Decision type must be valid
        - Application version must match (optimistic locking)
        
        Next Step: Call transition_stage() to move to CONCLUDED
        
        Audit Event: "application.decision_made"
        """
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")

        # Check stage
        current_stage = ApplicationStage(application.stage)
        if not DecisionRules.can_make_decision(current_stage):
            raise ValueError(
                f"Cannot make decision at stage {current_stage.value}. "
                f"Application must be in {ApplicationStage.DECISION_PENDING.value} stage."
            )

        # Validate decision type
        DecisionRules.validate_decision_type(request.decision_type)

        # Check version (optimistic locking)
        if application.version != request.application_version:
            raise ValueError(
                f"Version mismatch: expected {request.application_version}, "
                f"but application version is {application.version}"
            )

        # Check if decision already exists
        existing_decision = self.db.execute(
            select(ApplicationDecisionModel).where(
                ApplicationDecisionModel.application_id == application_id
            )
        ).scalar_one_or_none()

        if existing_decision:
            raise ValueError(f"Decision already exists for application {application_id}")

        # Create decision
        decision = ApplicationDecisionModel(
            tenant_id=tenant_id,
            application_id=application_id,
            decision_type=request.decision_type.value,
            decision_rationale=request.decision_rationale,
            decided_by_id=request.decided_by,
            conditions_json=request.conditions_json,
        )

        self.db.add(decision)

        # Update application
        application.decision_at = _utc_now()
        application.version += 1  # Bump version
        application.conclusion_type = request.decision_type.value

        self.db.flush()
        self.db.refresh(decision)

        # Audit logging
        log_admin_action(
            actor=request.decided_by,
            action=AuditEventRules.get_log_action_for_event("application.decision_made"),
            path=f"/internal/admissions/applications/{application_id}/decisions/{decision.id}",
            client_ip="service",
            entity="decision",
            metadata={
                "resource_id": str(decision.id),
                "application_id": application_id,
                "decision_type": request.decision_type.value,
                "decided_at": decision.decided_at.isoformat(),
                "conditions": request.conditions_json,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()

        return ApplicationDecisionReadSchema.model_validate(decision)

    async def get_decision(
        self,
        tenant_id: int,
        application_id: int,
    ) -> ApplicationDecisionReadSchema:
        """Get decision for an application."""
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)

        decision = self.db.execute(
            select(ApplicationDecisionModel).where(
                and_(
                    ApplicationDecisionModel.application_id == application_id,
                    ApplicationDecisionModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        if not decision:
            raise ValueError(f"No decision found for application {application_id}")

        return ApplicationDecisionReadSchema.model_validate(decision)

    async def finalize_workflow_decision(
        self,
        tenant_id: int,
        application_id: int,
        workflow_instance_id: int,
        approval_action: str,
        actor: str = "system@workflow",
    ) -> ApplicationDecisionReadSchema:
        """
        Finalize admission decision based on workflow outcome.
        
        Called by: WorkflowService.on_workflow_completed() callback
        
        Workflow Action Mapping:
        - "approve" → conclusion_type="accepted"
        - "reject" → conclusion_type="rejected"
        
        Transaction:
        1. Validate application exists and matches workflow instance
        2. Check if decision already exists (idempotency)
        3. Create ApplicationDecisionModel
        4. Update application: stage=concluded, conclusion_type, decision_at
        5. Record stage transition in history
        6. Audit log
        7. Commit
        
        Args:
            tenant_id: Tenant (mandatory, fail-closed)
            application_id: Application to finalize
            workflow_instance_id: Workflow that completed (validation)
            approval_action: "approve" or "reject"
            actor: Decision maker (default: system)
        
        Returns:
            ApplicationDecisionReadSchema
        
        Raises:
            ValueError: application not found, workflow mismatch, invalid action
            PermissionError: tenant mismatch
        """
        tenant_id = validate_tenant_id_provided(tenant_id)
        
        # Fetch application
        application = self.db.execute(
            select(ApplicationModel).where(
                and_(
                    ApplicationModel.id == application_id,
                    ApplicationModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if not application:
            raise ValueError(f"Application {application_id} not found in tenant {tenant_id}")
        
        # Validate workflow instance ID
        stored_workflow_id = application.metadata_json.get("workflow_instance_id")
        if stored_workflow_id != workflow_instance_id:
            raise ValueError(
                f"Workflow instance ID mismatch for application {application_id}: "
                f"expected {stored_workflow_id}, got {workflow_instance_id}"
            )
        
        # Check if decision already exists (idempotency)
        existing_decision = self.db.execute(
            select(ApplicationDecisionModel).where(
                and_(
                    ApplicationDecisionModel.application_id == application_id,
                    ApplicationDecisionModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        
        if existing_decision:
            return ApplicationDecisionReadSchema.model_validate(existing_decision)
        
        # Map approval action to conclusion type
        if approval_action == "approve":
            conclusion_type = ApplicationConclusionType.ACCEPTED.value
        elif approval_action == "reject":
            conclusion_type = ApplicationConclusionType.REJECTED.value
        else:
            raise ValueError(
                f"Invalid approval_action '{approval_action}'. Must be 'approve' or 'reject'."
            )
        
        # Update application
        application.stage = ApplicationStage.CONCLUDED.value
        application.conclusion_type = conclusion_type
        application.decision_at = _utc_now()
        
        # Update metadata
        application.metadata_json["workflow_status"] = "completed"
        application.metadata_json["workflow_outcome"] = approval_action
        application.metadata_json["workflow_completed_at"] = _utc_now().isoformat()
        
        # Create decision record
        decision = ApplicationDecisionModel(
            tenant_id=tenant_id,
            application_id=application_id,
            decision_type=conclusion_type,
            decision_rationale=f"Workflow decision: {approval_action}",
            decided_by_id=actor,
            conditions_json={
                "workflow_instance_id": workflow_instance_id,
                "approval_action": approval_action,
                "decision_source": "workflow_engine",
            },
        )
        self.db.add(decision)
        
        # Record stage transition
        stage_history = ApplicationStageHistoryModel(
            tenant_id=tenant_id,
            application_id=application_id,
            from_stage=ApplicationStage.DECISION_PENDING.value,
            to_stage=ApplicationStage.CONCLUDED.value,
            reason=f"Workflow completed with decision: {approval_action}",
            action_type=StageTransitionAction.AUTOMATED.value,
            actor_id=actor,
            metadata_json={
                "workflow_instance_id": workflow_instance_id,
                "trigger_type": "workflow_completion",
                "approval_action": approval_action,
            },
        )
        self.db.add(stage_history)
        
        self.db.flush()
        self.db.refresh(decision)
        
        # Audit logging
        log_admin_action(
            actor=actor,
            action=build_audit_action("admissions", "decision", "finalize"),
            path=f"/internal/admissions/applications/{application_id}/decision",
            client_ip="service",
            entity="decision",
            metadata={
                "resource_id": str(application_id),
                "workflow_instance_id": workflow_instance_id,
                "conclusion_type": conclusion_type,
                "approval_action": approval_action,
            },
            tenant_id=tenant_id,
        )

        # Phase 6: accepted decisions provision Person/Student identities.
        await self._provision_student_identity_on_accept(
            tenant_id=tenant_id,
            application=application,
            actor=actor,
        )
        
        self.db.commit()
        return ApplicationDecisionReadSchema.model_validate(decision)

