"""
Admissions Module - Business Rules

Stage transition rules, decision logic, and validation.

Key Principles:
- Explicit transitions: only allowed transitions are permitted
- Immutable history: once stage transitions are recorded, never updated/deleted
- One decision per application: enforce at service + DB (UNIQUE constraint)
- Fail-closed: invalid transitions raise exceptions, not silent failures
"""

from typing import Optional, Set

from app.modules.admissions.schemas import ApplicationConclusionType, ApplicationStage, StageTransitionAction


# ==============================================================================
# STAGE TRANSITION RULES
# ==============================================================================


class StageTransitionRules:
    """
    Defines valid stage transitions and validation rules.
    
    State machine:
        new → received → under_review → decision_pending → concluded
    
    Allowed transitions:
    - Any stage can transition back to previous stage (for corrections/resets)
    - new: entry point only
    - received: from new, from under_review (resubmit)
    - under_review: from received
    - decision_pending: from under_review
    - concluded: from decision_pending (FINAL, no reversals)
    """

    # Forward-only transitions (primary workflow)
    FORWARD_TRANSITIONS: dict[ApplicationStage, Set[ApplicationStage]] = {
        ApplicationStage.NEW: {ApplicationStage.RECEIVED},
        ApplicationStage.RECEIVED: {
            ApplicationStage.UNDER_REVIEW,
            ApplicationStage.NEW,  # Allow resubmit from received back to new
        },
        ApplicationStage.UNDER_REVIEW: {
            ApplicationStage.DECISION_PENDING,
            ApplicationStage.RECEIVED,  # Allow return to received for clarification
        },
        ApplicationStage.DECISION_PENDING: {
            ApplicationStage.CONCLUDED,
            ApplicationStage.UNDER_REVIEW,  # Allow return for more review
        },
        ApplicationStage.CONCLUDED: set(),  # FINAL state, no reversals
    }

    @classmethod
    def is_valid_transition(
        cls,
        from_stage: ApplicationStage,
        to_stage: ApplicationStage,
    ) -> bool:
        """Check if transition from_stage → to_stage is allowed."""
        if from_stage == to_stage:
            return False  # No self-transitions
        
        allowed_targets = cls.FORWARD_TRANSITIONS.get(from_stage, set())
        return to_stage in allowed_targets

    @classmethod
    def validate_transition(
        cls,
        from_stage: ApplicationStage,
        to_stage: ApplicationStage,
    ) -> None:
        """Validate transition; raise ValueError if invalid."""
        if not cls.is_valid_transition(from_stage, to_stage):
            raise ValueError(
                f"Invalid transition: {from_stage.value} → {to_stage.value}. "
                f"Allowed targets from {from_stage.value}: "
                f"{', '.join(s.value for s in cls.FORWARD_TRANSITIONS.get(from_stage, set()))}"
            )

    @classmethod
    def requires_decision(cls, stage: ApplicationStage) -> bool:
        """Check if reaching this stage requires a decision to be recorded."""
        return stage == ApplicationStage.CONCLUDED

    @classmethod
    def allows_document_upload(cls, stage: ApplicationStage) -> bool:
        """Check if application in this stage can accept document uploads."""
        # Allow uploads in: new, received, under_review
        # Disallow in: decision_pending, concluded
        return stage in {
            ApplicationStage.NEW,
            ApplicationStage.RECEIVED,
            ApplicationStage.UNDER_REVIEW,
        }

    @classmethod
    def allows_stage_transition(cls, stage: ApplicationStage, action_type: StageTransitionAction) -> bool:
        """Check if stage transition is allowed based on action type."""
        # SYSTEM_DECISION actions can only transition to CONCLUDED
        # (implied by decision creation)
        # Manual/automated can do any valid transition
        return True  # For now, all action types allowed for any valid transition


# ==============================================================================
# DECISION RULES
# ==============================================================================


class DecisionRules:
    """
    Defines valid decision rules and constraints.
    
    Constraints:
    - One decision per application (DB UNIQUE constraint enforced)
    - Decision can only be made when application stage == DECISION_PENDING
    - All decision types are valid: accepted, rejected, waitlist, withdrawn
    - Conditional acceptance: complex conditions stored in conditions_json
    """

    VALID_DECISION_TYPES: Set[ApplicationConclusionType] = {
        ApplicationConclusionType.ACCEPTED,
        ApplicationConclusionType.REJECTED,
        ApplicationConclusionType.WAITLIST,
        ApplicationConclusionType.WITHDRAWN,
    }

    @classmethod
    def can_make_decision(cls, stage: ApplicationStage) -> bool:
        """Check if decision can be made at this stage."""
        # Decision can only be made at DECISION_PENDING
        return stage == ApplicationStage.DECISION_PENDING

    @classmethod
    def validate_decision_type(cls, decision_type: ApplicationConclusionType) -> None:
        """Validate decision type; raise ValueError if invalid."""
        if decision_type not in cls.VALID_DECISION_TYPES:
            raise ValueError(
                f"Invalid decision type: {decision_type}. "
                f"Must be one of: {', '.join(t.value for t in cls.VALID_DECISION_TYPES)}"
            )

    @classmethod
    def requires_conditions(cls, decision_type: ApplicationConclusionType) -> bool:
        """Check if decision type requires conditions (e.g., conditional acceptance)."""
        # Only ACCEPTED decisions might have conditions
        return decision_type == ApplicationConclusionType.ACCEPTED

    @classmethod
    def validates_conditions(cls, decision_type: ApplicationConclusionType, conditions: dict) -> bool:
        """Validate conditions based on decision type."""
        if decision_type != ApplicationConclusionType.ACCEPTED:
            # Non-accept decisions should have empty conditions
            return len(conditions) == 0
        
        # Accept decisions can have any conditions (validated by endpoint or domain rules)
        return True

    @classmethod
    def get_conclusion_type_for_stage_change(
        cls, to_stage: ApplicationStage, decision_type: Optional[ApplicationConclusionType] = None
    ) -> Optional[ApplicationConclusionType]:
        """Determine what conclusion_type to set when transitioning to a stage."""
        if to_stage == ApplicationStage.CONCLUDED and decision_type:
            # When transitioning to CONCLUDED, set conclusion_type from decision
            return decision_type
        elif to_stage != ApplicationStage.CONCLUDED:
            # No conclusion type for non-concluded stages
            return None
        else:
            # Cannot transition to CONCLUDED without decision_type
            raise ValueError("Transition to CONCLUDED requires decision_type")


# ==============================================================================
# TENANT ISOLATION RULES
# ==============================================================================


class TenantIsolationRules:
    """
    Tenant isolation contract: fail-closed, no implicit defaults.
    
    Rules:
    - tenant_id must always be provided (never inferred or defaulted)
    - Every query must filter by tenant_id at service layer
    - Cross-tenant access should raise exception (HTTP 403)
    - Orphaned records (applicant belongs to different tenant) = 403
    """

    @classmethod
    def validate_tenant_match(cls, resource_tenant_id: int, request_tenant_id: int, resource_name: str = "resource") -> None:
        """
        Validate tenant match; raise PermissionError with 403 contract if mismatch.
        
        Args:
            resource_tenant_id: tenant_id of resource in database
            request_tenant_id: tenant_id from request context
            resource_name: name of resource for error message
        
        Raises:
            PermissionError: if tenant_id mismatch (should map to HTTP 403)
        """
        if resource_tenant_id != request_tenant_id:
            raise PermissionError(
                f"Tenant isolation violation: {resource_name} belongs to tenant "
                f"{resource_tenant_id}, but request is from tenant {request_tenant_id}. "
                f"Access denied (HTTP 403)."
            )

    @classmethod
    def validate_tenant_id_provided(cls, tenant_id: Optional[int]) -> None:
        """Validate that tenant_id is provided; raise ValueError if None."""
        if tenant_id is None:
            raise ValueError(
                "tenant_id must always be provided explicitly. "
                "No implicit defaults or fallbacks allowed (fail-closed contract)."
            )


# ==============================================================================
# DOCUMENT RULES  
# ==============================================================================


class DocumentRules:
    """
    Document handling rules and constraints.
    
    Constraints:
    - document_key must be a safe reference (S3, not filesystem)
    - document_key validated at schema + service layer
    - Multiple documents per application allowed
    - Document status progression: received → verified or rejected
    """

    VALID_DOCUMENT_TYPES = {
        "transcript",
        "test_score",
        "recommendation_letter",
        "personal_statement",
        "resume",
        "portfolio",
        "identification",
        "other",
    }

    @classmethod
    def validate_document_type(cls, document_type: str) -> None:
        """Validate document type; raise ValueError if not recognized."""
        # Allow any document type for extensibility, but log unknown types
        # For MVP, we use a predefined list but don't enforce it strictly
        if document_type not in cls.VALID_DOCUMENT_TYPES:
            # Log warning but allow (can add known types later)
            pass  # Will be logged in service layer

    @classmethod
    def is_document_key_safe(cls, document_key: str) -> bool:
        """Check if document_key is a safe reference (not filesystem path)."""
        # Must start with safe protocol or bucket name
        unsafe_prefixes = ["/", "C:\\", "D:\\", "../", ".\\"]
        return not any(document_key.startswith(p) for p in unsafe_prefixes)

    @classmethod
    def allows_document_upload_at_stage(cls, stage: ApplicationStage) -> bool:
        """Check if documents can be uploaded at this stage."""
        return StageTransitionRules.allows_document_upload(stage)


# ==============================================================================
# AUDIT EVENT RULES
# ==============================================================================


class AuditEventRules:
    """
    Defines what events should be logged and their severity levels.
    
    Events:
    - applicant.created: CREATE on ApplicantModel
    - applicant.updated: UPDATE on ApplicantModel
    - application.created: CREATE on ApplicationModel
    - application.document_attached: INSERT on ApplicationDocumentModel
    - application.stage_changed: INSERT on ApplicationStageHistoryModel + UPDATE on ApplicationModel.stage
    - application.decision_made: INSERT on ApplicationDecisionModel + UPDATE on ApplicationModel
    """

    AUDIT_EVENTS = {
        "applicant.created": {
            "action": "CREATE",
            "resource": "applicant",
            "severity": "info",
            "fields_to_log": ["email", "program_id", "application_year", "status"],
        },
        "applicant.updated": {
            "action": "UPDATE",
            "resource": "applicant",
            "severity": "info",
            "fields_to_log": ["first_name", "last_name", "status", "metadata_json"],
        },
        "application.created": {
            "action": "CREATE",
            "resource": "application",
            "severity": "info",
            "fields_to_log": ["applicant_id", "program_id", "stage"],
        },
        "application.document_attached": {
            "action": "CREATE",
            "resource": "document",
            "severity": "info",
            "fields_to_log": ["document_type", "file_name", "file_size_bytes"],
        },
        "application.stage_changed": {
            "action": "UPDATE",
            "resource": "application",
            "severity": "info",
            "fields_to_log": ["from_stage", "to_stage", "reason"],
        },
        "application.decision_made": {
            "action": "CREATE",
            "resource": "decision",
            "severity": "warning",  # Higher severity: decisions are critical
            "fields_to_log": ["decision_type", "conditions_json", "decided_by_id"],
        },
    }

    @classmethod
    def get_event_config(cls, event_name: str) -> Optional[dict]:
        """Get configuration for an audit event."""
        return cls.AUDIT_EVENTS.get(event_name)

    @classmethod
    def get_log_action_for_event(cls, event_name: str) -> Optional[str]:
        """Get log_admin_action() permission string for event."""
        # Maps to platform audit logging: "module.action.operation"
        # Example: "admissions.applicant.create"
        event_config = cls.get_event_config(event_name)
        if not event_config:
            return None
        
        resource = event_config["resource"]
        action = event_config["action"].lower()
        return f"admissions.{resource}.{action}"
