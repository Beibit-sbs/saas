"""
Notification Center Service Contract

L2 deterministic service contract for tenant-safe notification management.
CRITICAL: Tenant isolation required. No actual sending, no provider calls.
"""

from typing import Dict, Any

# ============================================================================
# FSM/Status Constants
# ============================================================================

NOTIFICATION_TYPE = {
    "WORKFLOW_APPROVED": "Workflow has been approved by human reviewer",
    "WORKFLOW_REJECTED": "Workflow has been rejected during review",
    "WORKLOAD_ASSIGNED": "Workload has been assigned to staff",
    "REVIEW_NEEDED": "Human review is needed for item",
    "CHANGE_APPLIED": "Timetable change has been applied successfully",
}

NOTIFICATION_STATUS = {
    "QUEUED": "Notification is queued",
    "COMPOSED": "Notification message is composed",
    "READY_FOR_DISPATCH": "Notification is ready to send (not sent)",
    "SEND_FAILED": "Send attempt failed (L2: no actual sending)",
}

# CRITICAL SAFETY FLAGS
NO_SENDING = True
NO_PROVIDER_CALLS = True
TENANT_ISOLATION_REQUIRED = True

# ============================================================================
# Safety Flags
# ============================================================================

SAFETY_FLAGS = {
    "no_api_claim": True,
    "no_frontend_claim": True,
    "no_brain_claim": True,
    "no_actual_sending": True,
    "no_email_provider_calls": True,
    "no_sms_provider_calls": True,
    "no_push_provider_calls": True,
    "no_cross_tenant_broadcast": True,
    "tenant_isolation_required": True,
    "no_autonomous_execution": True,
    "no_kpi_lineage_claim": True,
    "no_e2e_claim": True,
    "target_level": "L3",
}


# ============================================================================
# Tenant Validation (CRITICAL - Highest Priority)
# ============================================================================

def validate_notification_tenant(tenant_id: Any) -> bool:
    """
    Validate tenant_id for notification access.
    CRITICAL: Fail-closed on any invalid tenant_id.
    Reject None, non-positive, non-integer.

    Args:
        tenant_id: Claimed tenant identifier

    Returns:
        bool: True if valid, False if invalid
    """
    if tenant_id is None:
        return False
    if not isinstance(tenant_id, int):
        return False
    if tenant_id <= 0:
        return False
    return True


# ============================================================================
# Service Contracts
# ============================================================================

def build_notification_contract(tenant_id: Any, notification_type: Any) -> Dict[str, Any]:
    """
    Build deterministic notification contract (no sending).
    CRITICAL: All outputs must include tenant_id scope.

    Args:
        tenant_id: Tenant identifier for scoping (CRITICAL)
        notification_type: Type of notification

    Returns:
        Dictionary with notification contract
    """
    if not validate_notification_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "notification_center",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id - access denied",
        }

    # Ensure notification_type is valid
    if notification_type not in NOTIFICATION_TYPE and notification_type is not None:
        return {
            "tenant_id": tenant_id,
            "module": "notification_center",
            "error": "Invalid notification_type",
        }

    return {
        "tenant_id": tenant_id,  # CRITICAL: scope all output
        "module": "notification_center",
        "notification_type": notification_type or "UNKNOWN",
        "notification_status": "COMPOSED",
        "ready_for_dispatch": True,
        "actually_sent": False,
        "provider_called": False,
        "cross_tenant_broadcast": False,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_readonly_notification_compose",
    }


def get_notification_types(tenant_id: Any = None) -> Dict[str, Any]:
    """
    Return available notification types (with optional tenant scoping).

    Args:
        tenant_id: Optional tenant identifier for scoping

    Returns:
        Dictionary with notification types
    """
    if tenant_id is not None and not validate_notification_tenant(tenant_id):
        return {"error": "Invalid tenant_id"}

    return {
        "valid": True,
        "notification_types": NOTIFICATION_TYPE,
        "notification_statuses": NOTIFICATION_STATUS,
        "tenant_scoped": tenant_id is not None,
        "tenant_id": tenant_id if tenant_id is not None else "N/A",
        "safety_flags": SAFETY_FLAGS,
    }


def get_notification_readiness_contract(tenant_id: Any) -> Dict[str, Any]:
    """
    Return notification L2 readiness contract (CRITICAL tenant isolation).

    Args:
        tenant_id: Tenant identifier for scoping

    Returns:
        Dictionary with notification readiness
    """
    if not validate_notification_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "notification_center",
            "readiness_status": "TENANT_VALIDATION_FAILED",
            "error": "Invalid tenant_id",
        }

    return {
        "tenant_id": tenant_id,  # CRITICAL: always included
        "module": "notification_center",
        "readiness_status": "L2_CONTRACT_READY",
        "evidence_level": "L2",
        "target_level": "L2",
        "valid_notification_types": list(NOTIFICATION_TYPE.keys()),
        "valid_notification_statuses": list(NOTIFICATION_STATUS.keys()),
        "actual_sending": NO_SENDING,
        "provider_calls_made": NO_PROVIDER_CALLS,
        "tenant_isolation": TENANT_ISOLATION_REQUIRED,
        "cross_tenant_broadcast": False,
        "safety_flags": SAFETY_FLAGS,
        "contract_type": "deterministic_tenant_isolated_notification",
        "critical_note": "Tenant isolation is MANDATORY for all operations",
    }


def classify_notification_readiness(tenant_id: Any, notification_payload: Any) -> Dict[str, Any]:
    """Deterministically classify notification readiness at L3."""
    if not validate_notification_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "notification_center",
            "maturity_level": "L3",
            "notification_readiness_status": "NOTIFICATION_INPUT_INCOMPLETE",
            "classification": "NOTIFICATION_INPUT_INCOMPLETE",
            "NO_SENDING": NO_SENDING,
            "NO_PROVIDER_CALLS": NO_PROVIDER_CALLS,
            "TENANT_ISOLATION_REQUIRED": TENANT_ISOLATION_REQUIRED,
            "safety_flags": SAFETY_FLAGS,
        }

    payload = notification_payload if isinstance(notification_payload, dict) else {}
    required_fields = ["notification_type", "subject", "message"]
    missing_fields = [field for field in required_fields if payload.get(field) in (None, "")]
    notification_type = str(payload.get("notification_type") or "").upper()
    provider_configured = bool(payload.get("provider_configured") or payload.get("dispatch_provider_ready"))
    send_requested = bool(payload.get("send_requested") or payload.get("dispatch_now"))

    if missing_fields:
        status = "NOTIFICATION_INPUT_INCOMPLETE"
        next_step = "COMPLETE_REQUIRED_FIELDS"
    elif notification_type not in set(NOTIFICATION_TYPE.keys()):
        status = "BLOCKED_UNSUPPORTED_TYPE"
        next_step = "SELECT_SUPPORTED_NOTIFICATION_TYPE"
    elif not provider_configured:
        status = "PROVIDER_NOT_CONFIGURED"
        next_step = "CONFIGURE_PROVIDER_FOR_MANUAL_REVIEW"
    elif send_requested:
        status = "READY_FOR_MANUAL_DISPATCH_REVIEW"
        next_step = "HUMAN_DISPATCH_REVIEW"
    else:
        status = "READY_TO_COMPOSE"
        next_step = "COMPOSE_PREVIEW"

    return {
        "tenant_id": tenant_id,
        "module": "notification_center",
        "maturity_level": "L3",
        "notification_readiness_status": status,
        "classification": status,
        "notification_type": notification_type or "UNKNOWN",
        "missing_fields": missing_fields,
        "NO_SENDING": NO_SENDING,
        "NO_PROVIDER_CALLS": NO_PROVIDER_CALLS,
        "TENANT_ISOLATION_REQUIRED": TENANT_ISOLATION_REQUIRED,
        "no_sending": NO_SENDING,
        "no_provider_calls": NO_PROVIDER_CALLS,
        "tenant_isolation_required": TENANT_ISOLATION_REQUIRED,
        "cross_tenant_broadcast": False,
        "frontend_claim": False,
        "kpi_values_available": False,
        "brain_mapping_status": "NOT_AVAILABLE",
        "next_recommended_step": next_step,
        "safety_flags": SAFETY_FLAGS,
    }


def get_notification_visibility_summary(tenant_id: Any) -> Dict[str, Any]:
    """Build deterministic read-only L4 visibility summary for notification readiness."""
    if not validate_notification_tenant(tenant_id):
        return {
            "tenant_id": None,
            "module": "notification_center",
            "visibility_level": "L4",
            "operational_status": "TENANT_VALIDATION_FAILED",
            "classification": "NOTIFICATION_INPUT_INCOMPLETE",
            "allowed_actions": ["PREVIEW", "CLASSIFY", "REVIEW"],
            "forbidden_actions": ["SEND", "PROVIDER_CALL", "AUTO_DISPATCH", "CROSS_TENANT_BROADCAST"],
            "safety_flags": SAFETY_FLAGS,
            "evidence_notes": ["tenant validation failed"],
            "no_autonomous_execution": True,
            "readonly": True,
            "tenant_scoped": True,
        }

    evaluated = classify_notification_readiness(
        int(tenant_id),
        {"notification_type": "REVIEW_NEEDED", "subject": "review", "message": "review", "provider_configured": True},
    )
    return {
        "tenant_id": int(tenant_id),
        "module": "notification_center",
        "visibility_level": "L4",
        "operational_status": str(evaluated.get("notification_readiness_status") or "READY_TO_COMPOSE"),
        "classification": str(evaluated.get("classification") or "READY_TO_COMPOSE"),
        "allowed_actions": ["PREVIEW", "CLASSIFY", "REVIEW"],
        "forbidden_actions": ["SEND", "PROVIDER_CALL", "AUTO_DISPATCH", "CROSS_TENANT_BROADCAST"],
        "safety_flags": SAFETY_FLAGS,
        "evidence_notes": [
            "deterministic notification readiness surfaced via read-only L4 visibility",
            "no provider calls and no dispatch performed",
        ],
        "no_autonomous_execution": True,
        "readonly": True,
        "tenant_scoped": True,
    }
