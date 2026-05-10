"""
Admissions Workflow Completion Callback Handler

Handles workflow completion for admission_application entities.

Responsibility:
- Map workflow outcome to approval_action
- Call DecisionService.finalize_workflow_decision()
- Handle idempotency
- Audit logging
- Tenant isolation
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import validate_tenant_id_provided
from app.modules.workflows.callback_handler import WorkflowCompletionCallbackHandler


class AdmissionsWorkflowCompletionCallbackHandler(WorkflowCompletionCallbackHandler):
    """
    Callback handler for admission_application workflow completion.

    Maps workflow outcome to decision and calls DecisionService.
    Idempotent: safe to call multiple times.
    """

    def __init__(self, db_session_factory: Callable[[], Session]):
        """
        Args:
            db_session_factory: Callable that returns a new Session
        """
        self.db_session_factory = db_session_factory

    async def handle(
        self,
        workflow_id: int,
        tenant_id: int,
        entity_type: str,
        entity_id: int,
        workflow_key: str,
        outcome: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle admission workflow completion.

        Maps workflow outcome to approval_action and finalizes decision.
        """
        # Fail-closed: validate tenant
        tenant_id = validate_tenant_id_provided(tenant_id)

        # Validate entity type
        if entity_type != "admission_application":
            raise ValueError(
                f"AdmissionsWorkflowCompletionCallbackHandler: "
                f"Invalid entity_type '{entity_type}'. Expected 'admission_application'"
            )

        # Extract approval_action from outcome
        approval_action = self._extract_approval_action(outcome)
        if not approval_action:
            # Outcome missing action: fail-closed
            raise ValueError(
                f"Workflow {workflow_id}: outcome_data missing 'action' field. "
                f"Expected 'approve' or 'reject', got: {outcome}"
            )

        # Get fresh session
        db = self.db_session_factory()

        # Import here to avoid circular dependency
        from app.modules.admissions.service import DecisionService

        try:
            decision_service = DecisionService(db)

            # Call decision service (idempotency check happens inside)
            decision = await decision_service.finalize_workflow_decision(
                tenant_id=tenant_id,
                application_id=entity_id,
                workflow_instance_id=workflow_id,
                approval_action=approval_action,
                actor="system@workflow",
            )

            return {
                "status": "success",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "result_id": decision.id,
                "message": f"Admissions decision finalized from workflow outcome (action={approval_action})",
            }

        except ValueError as e:
            # Check if decision already exists (idempotency)
            error_msg = str(e).lower()
            if "already exists" in error_msg or "idempotent" in error_msg:
                # Already finalized on previous attempt: safe to return success
                return {
                    "status": "no_action",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "result_id": None,
                    "message": f"Decision already finalized for application {entity_id} (idempotent skip)",
                }
            # Validation error: propagate (fail-closed)
            raise
        finally:
            db.close()

    @staticmethod
    def _extract_approval_action(outcome: dict | None) -> str | None:
        """
        Extract approval_action from workflow outcome.

        Safe extraction with validation.

        Returns:
            "approve" | "reject" | None
        """
        if not isinstance(outcome, dict):
            return None

        action = outcome.get("action")
        if isinstance(action, str) and action in ("approve", "reject"):
            return action

        return None
