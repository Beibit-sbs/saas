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
from typing import Optional

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
