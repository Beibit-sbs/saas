"""
Workflow Completion Callback Handler Interface

Design Principles:
- Entity-type dispatcher pattern
- Decoupled from specific service implementations
- Idempotent and fail-closed
- Tenant-first validation
- Audit logging integration
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from sqlalchemy.orm import Session


class WorkflowCompletionCallbackHandler(ABC):
    """
    Abstract interface for handling workflow completion callbacks.
    
    Implementations are responsible for:
    - Entity type validation
    - Outcome mapping
    - Service dispatch
    - Idempotency safeguards
    - Audit logging
    
    Pattern: Strategy pattern for dispatching by entity_type.
    """

    @abstractmethod
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
        Handle workflow completion callback.
        
        Args:
            workflow_id: Workflow instance ID
            tenant_id: Workspace tenant (mandatory)
            entity_type: Type of entity (e.g., "admission_application")
            entity_id: Entity ID (e.g., application_id)
            workflow_key: Workflow key (e.g., "admissions")
            outcome: Workflow outcome data {
                "action": "approve"|"reject"|None,
                "reason": str,
                "metadata": dict,
            }
        
        Returns:
            {
                "status": "success" | "no_action" | "skipped",
                "entity_type": str,
                "entity_id": int,
                "result_id": int | None,  # e.g., decision_id
                "message": str,
            }
        
        Raises:
            ValueError: Invalid inputs, validation failures
            PermissionError: Tenant mismatch
        """
        pass


class CallbackHandlerRegistry:
    """
    Registry for workflow completion callback handlers.
    
    Dispatches callbacks to appropriate handler based on entity_type.
    
    Uses strategy pattern: entity_type → handler mapping.
    """

    def __init__(self):
        self._handlers: dict[str, WorkflowCompletionCallbackHandler] = {}

    def register(
        self,
        entity_type: str,
        handler: WorkflowCompletionCallbackHandler,
    ) -> None:
        """Register handler for entity type."""
        if not entity_type or not entity_type.strip():
            raise ValueError("entity_type must be non-empty")
        if not isinstance(handler, WorkflowCompletionCallbackHandler):
            raise TypeError("handler must implement WorkflowCompletionCallbackHandler")
        
        self._handlers[entity_type.strip()] = handler

    async def dispatch(
        self,
        workflow_id: int,
        tenant_id: int,
        entity_type: str,
        entity_id: int,
        workflow_key: str,
        outcome: dict | None = None,
    ) -> dict[str, Any]:
        """
        Dispatch callback to registered handler.
        
        If no handler registered, returns no_action (safe unknown entity).
        """
        handler = self._handlers.get(entity_type)
        if not handler:
            # Unknown entity type: ignore safely
            return {
                "status": "no_action",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "result_id": None,
                "message": f"No callback handler registered for entity_type '{entity_type}'",
            }
        
        # Dispatch to handler
        return await handler.handle(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            workflow_key=workflow_key,
            outcome=outcome,
        )


# Global registry instance (singleton)
_global_callback_registry: CallbackHandlerRegistry | None = None


def get_callback_registry() -> CallbackHandlerRegistry:
    """Get or create global callback registry."""
    global _global_callback_registry
    if _global_callback_registry is None:
        _global_callback_registry = CallbackHandlerRegistry()
    return _global_callback_registry


def initialize_callback_registry(db_session_factory: Callable[[], Session]) -> None:
    """
    Initialize callback registry with all handlers.
    
    Called during application startup to register all callback handlers.
    
    Args:
        db_session_factory: Callable that returns a new DB session
    """
    from app.modules.workflows.callbacks.admissions_callback import (
        AdmissionsWorkflowCompletionCallbackHandler,
    )
    
    registry = get_callback_registry()
    
    # Register admissions callback handler
    admissions_handler = AdmissionsWorkflowCompletionCallbackHandler(
        db_session_factory=db_session_factory
    )
    registry.register("admission_application", admissions_handler)
