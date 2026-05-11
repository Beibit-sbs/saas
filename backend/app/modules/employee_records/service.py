"""Employee Records Foundation Service Contract - A-027.2 L2."""

MODULE_NAME = "employee_records"
UCE_ID = "UCE-003"
TARGET_LEVEL = "L2"
EXPANSION_LAYER = "university_completeness"


def get_employee_records_foundation_contract(tenant_id: int, payload: dict | None = None) -> dict:
    """
    Return L2 foundation contract for employee records.
    
    Tenant validation:
    - None/0/-1 rejected
    - positive int accepted
    
    No provider calls, no autonomy, deterministic only.
    No payroll mutations in foundation.
    """
    
    # Tenant fail-closed validation
    if not tenant_id or tenant_id <= 0:
        raise ValueError(f"invalid_tenant_id: {tenant_id}")
    
    return {
        "tenant_id": tenant_id,
        "module": MODULE_NAME,
        "uce_id": UCE_ID,
        "maturity_level": "L2",
        "expansion_layer": EXPANSION_LAYER,
        "contract_status": "FOUNDATION_READY",
        "service_contract_ready": True,
        "tenant_scoped": True,
        "deterministic": True,
        "lifecycle_statuses": [
            "ACTIVE",
            "UPDATE_PENDING",
            "VERIFICATION_REQUIRED",
            "ARCHIVED",
        ],
        "allowed_actions": [
            "CREATE_EMPLOYEE_RECORD",
            "VIEW_EMPLOYEE_RECORD",
            "SUBMIT_RECORD_UPDATE",
            "REQUEST_VERIFICATION",
        ],
        "forbidden_actions": [
            "AUTO_CHANGE_EMPLOYEE_RECORD",
            "AUTO_DELETE_RECORD",
            "AUTO_CHANGE_POSITION",
            "AUTO_CALCULATE_PAYROLL",
        ],
        "required_evidence": [
            "employee_id",
            "hire_date",
            "employment_type",
        ],
        "next_maturity_gap": "L3 deterministic logic: employment state validation, record reconciliation",
        "safety_flags": {
            "no_api_claim": True,
            "no_frontend_claim": True,
            "no_live_integration_claim": True,
            "no_provider_call": True,
            "no_kpi_claim": True,
            "no_brain_claim": True,
            "no_autonomous_execution": True,
            "no_external_side_effects": True,
            "no_l3_claim": True,
            "no_l4_claim": True,
            "no_l5_claim": True,
            "no_l6_claim": True,
        },
    }
