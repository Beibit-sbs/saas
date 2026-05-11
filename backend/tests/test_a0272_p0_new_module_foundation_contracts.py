"""A-027.2 P0 New Module Foundation Contracts - Targeted Tests."""

import pytest


# ===== TEST GROUP 1: IMPORT VALIDATION =====

def test_import_all_a0272_services():
    """Verify all A-027.2 module services import successfully."""
    from app.modules.staff_recruitment.service import get_staff_recruitment_foundation_contract
    from app.modules.staff_onboarding.service import get_staff_onboarding_foundation_contract
    from app.modules.employee_records.service import get_employee_records_foundation_contract
    from app.modules.document_workflow.service import get_document_workflow_foundation_contract
    from app.modules.order_decree_registry.service import get_order_decree_registry_foundation_contract
    from app.modules.curriculum_mapping.service import get_curriculum_mapping_foundation_contract
    from app.modules.syllabus_management.service import get_syllabus_management_foundation_contract
    from app.modules.international_office.service import get_international_office_foundation_contract
    from app.modules.program_learning_outcomes.service import get_program_learning_outcomes_foundation_contract
    from app.modules.course_learning_outcomes.service import get_course_learning_outcomes_foundation_contract
    from app.modules.committee_decision_registry.service import get_committee_decision_registry_foundation_contract
    
    # Verify all functions are callable
    assert callable(get_staff_recruitment_foundation_contract)
    assert callable(get_staff_onboarding_foundation_contract)
    assert callable(get_employee_records_foundation_contract)
    assert callable(get_document_workflow_foundation_contract)
    assert callable(get_order_decree_registry_foundation_contract)
    assert callable(get_curriculum_mapping_foundation_contract)
    assert callable(get_syllabus_management_foundation_contract)
    assert callable(get_international_office_foundation_contract)
    assert callable(get_program_learning_outcomes_foundation_contract)
    assert callable(get_course_learning_outcomes_foundation_contract)
    assert callable(get_committee_decision_registry_foundation_contract)


# ===== TEST GROUP 2: TENANT FAIL-CLOSED VALIDATION =====

def test_tenant_fail_closed_staff_recruitment():
    """Verify staff_recruitment rejects invalid tenants."""
    from app.modules.staff_recruitment.service import get_staff_recruitment_foundation_contract
    
    with pytest.raises(ValueError):
        get_staff_recruitment_foundation_contract(None)
    with pytest.raises(ValueError):
        get_staff_recruitment_foundation_contract(0)
    with pytest.raises(ValueError):
        get_staff_recruitment_foundation_contract(-1)
    
    # Valid tenant should succeed
    contract = get_staff_recruitment_foundation_contract(1)
    assert contract is not None
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_staff_onboarding():
    """Verify staff_onboarding rejects invalid tenants."""
    from app.modules.staff_onboarding.service import get_staff_onboarding_foundation_contract
    
    with pytest.raises(ValueError):
        get_staff_onboarding_foundation_contract(None)
    with pytest.raises(ValueError):
        get_staff_onboarding_foundation_contract(0)
    with pytest.raises(ValueError):
        get_staff_onboarding_foundation_contract(-1)
    
    contract = get_staff_onboarding_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_employee_records():
    """Verify employee_records rejects invalid tenants."""
    from app.modules.employee_records.service import get_employee_records_foundation_contract
    
    with pytest.raises(ValueError):
        get_employee_records_foundation_contract(None)
    with pytest.raises(ValueError):
        get_employee_records_foundation_contract(0)
    with pytest.raises(ValueError):
        get_employee_records_foundation_contract(-1)
    
    contract = get_employee_records_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_document_workflow():
    """Verify document_workflow rejects invalid tenants."""
    from app.modules.document_workflow.service import get_document_workflow_foundation_contract
    
    with pytest.raises(ValueError):
        get_document_workflow_foundation_contract(None)
    with pytest.raises(ValueError):
        get_document_workflow_foundation_contract(0)
    with pytest.raises(ValueError):
        get_document_workflow_foundation_contract(-1)
    
    contract = get_document_workflow_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_order_decree():
    """Verify order_decree_registry rejects invalid tenants."""
    from app.modules.order_decree_registry.service import get_order_decree_registry_foundation_contract
    
    with pytest.raises(ValueError):
        get_order_decree_registry_foundation_contract(None)
    with pytest.raises(ValueError):
        get_order_decree_registry_foundation_contract(0)
    with pytest.raises(ValueError):
        get_order_decree_registry_foundation_contract(-1)
    
    contract = get_order_decree_registry_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_curriculum_mapping():
    """Verify curriculum_mapping rejects invalid tenants."""
    from app.modules.curriculum_mapping.service import get_curriculum_mapping_foundation_contract
    
    with pytest.raises(ValueError):
        get_curriculum_mapping_foundation_contract(None)
    with pytest.raises(ValueError):
        get_curriculum_mapping_foundation_contract(0)
    with pytest.raises(ValueError):
        get_curriculum_mapping_foundation_contract(-1)
    
    contract = get_curriculum_mapping_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_syllabus_management():
    """Verify syllabus_management rejects invalid tenants."""
    from app.modules.syllabus_management.service import get_syllabus_management_foundation_contract
    
    with pytest.raises(ValueError):
        get_syllabus_management_foundation_contract(None)
    with pytest.raises(ValueError):
        get_syllabus_management_foundation_contract(0)
    with pytest.raises(ValueError):
        get_syllabus_management_foundation_contract(-1)
    
    contract = get_syllabus_management_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_international_office():
    """Verify international_office rejects invalid tenants."""
    from app.modules.international_office.service import get_international_office_foundation_contract
    
    with pytest.raises(ValueError):
        get_international_office_foundation_contract(None)
    with pytest.raises(ValueError):
        get_international_office_foundation_contract(0)
    with pytest.raises(ValueError):
        get_international_office_foundation_contract(-1)
    
    contract = get_international_office_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_program_learning_outcomes():
    """Verify program_learning_outcomes rejects invalid tenants."""
    from app.modules.program_learning_outcomes.service import get_program_learning_outcomes_foundation_contract
    
    with pytest.raises(ValueError):
        get_program_learning_outcomes_foundation_contract(None)
    with pytest.raises(ValueError):
        get_program_learning_outcomes_foundation_contract(0)
    with pytest.raises(ValueError):
        get_program_learning_outcomes_foundation_contract(-1)
    
    contract = get_program_learning_outcomes_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_course_learning_outcomes():
    """Verify course_learning_outcomes rejects invalid tenants."""
    from app.modules.course_learning_outcomes.service import get_course_learning_outcomes_foundation_contract
    
    with pytest.raises(ValueError):
        get_course_learning_outcomes_foundation_contract(None)
    with pytest.raises(ValueError):
        get_course_learning_outcomes_foundation_contract(0)
    with pytest.raises(ValueError):
        get_course_learning_outcomes_foundation_contract(-1)
    
    contract = get_course_learning_outcomes_foundation_contract(1)
    assert contract["tenant_id"] == 1


def test_tenant_fail_closed_committee_decision():
    """Verify committee_decision_registry rejects invalid tenants."""
    from app.modules.committee_decision_registry.service import get_committee_decision_registry_foundation_contract
    
    with pytest.raises(ValueError):
        get_committee_decision_registry_foundation_contract(None)
    with pytest.raises(ValueError):
        get_committee_decision_registry_foundation_contract(0)
    with pytest.raises(ValueError):
        get_committee_decision_registry_foundation_contract(-1)
    
    contract = get_committee_decision_registry_foundation_contract(1)
    assert contract["tenant_id"] == 1


# ===== TEST GROUP 3: FOUNDATION OUTPUT VALIDATION =====

@pytest.mark.parametrize("module_import,module_name,uce_id", [
    ("app.modules.staff_recruitment.service", "get_staff_recruitment_foundation_contract", "UCE-001"),
    ("app.modules.staff_onboarding.service", "get_staff_onboarding_foundation_contract", "UCE-002"),
    ("app.modules.employee_records.service", "get_employee_records_foundation_contract", "UCE-003"),
    ("app.modules.document_workflow.service", "get_document_workflow_foundation_contract", "UCE-009"),
    ("app.modules.order_decree_registry.service", "get_order_decree_registry_foundation_contract", "UCE-011"),
    ("app.modules.curriculum_mapping.service", "get_curriculum_mapping_foundation_contract", "UCE-014"),
    ("app.modules.syllabus_management.service", "get_syllabus_management_foundation_contract", "UCE-015"),
    ("app.modules.international_office.service", "get_international_office_foundation_contract", "UCE-019"),
    ("app.modules.program_learning_outcomes.service", "get_program_learning_outcomes_foundation_contract", "UCE-071"),
    ("app.modules.course_learning_outcomes.service", "get_course_learning_outcomes_foundation_contract", "UCE-072"),
    ("app.modules.committee_decision_registry.service", "get_committee_decision_registry_foundation_contract", "UCE-090"),
])
def test_foundation_output_structure(module_import, module_name, uce_id):
    """Verify foundation contract output structure for all modules."""
    import importlib
    mod = importlib.import_module(module_import)
    func = getattr(mod, module_name)
    
    contract = func(1)
    
    # Required fields
    assert isinstance(contract, dict)
    assert contract["tenant_id"] == 1
    assert contract["module"] is not None
    assert contract["uce_id"] == uce_id
    assert contract["maturity_level"] == "L2"
    assert contract["expansion_layer"] == "university_completeness"
    assert contract["service_contract_ready"] is True
    assert contract["tenant_scoped"] is True
    assert contract["deterministic"] is True


# ===== TEST GROUP 4: LIFECYCLE/STATUS VALIDATION =====

@pytest.mark.parametrize("module_import,module_name", [
    ("app.modules.staff_recruitment.service", "get_staff_recruitment_foundation_contract"),
    ("app.modules.staff_onboarding.service", "get_staff_onboarding_foundation_contract"),
    ("app.modules.employee_records.service", "get_employee_records_foundation_contract"),
    ("app.modules.document_workflow.service", "get_document_workflow_foundation_contract"),
    ("app.modules.order_decree_registry.service", "get_order_decree_registry_foundation_contract"),
    ("app.modules.curriculum_mapping.service", "get_curriculum_mapping_foundation_contract"),
    ("app.modules.syllabus_management.service", "get_syllabus_management_foundation_contract"),
    ("app.modules.international_office.service", "get_international_office_foundation_contract"),
    ("app.modules.program_learning_outcomes.service", "get_program_learning_outcomes_foundation_contract"),
    ("app.modules.course_learning_outcomes.service", "get_course_learning_outcomes_foundation_contract"),
    ("app.modules.committee_decision_registry.service", "get_committee_decision_registry_foundation_contract"),
])
def test_lifecycle_status_validation(module_import, module_name):
    """Verify lifecycle, actions, and evidence for all modules."""
    import importlib
    mod = importlib.import_module(module_import)
    func = getattr(mod, module_name)
    
    contract = func(1)
    
    # Required collections
    assert "lifecycle_statuses" in contract
    assert len(contract["lifecycle_statuses"]) > 0
    assert all(isinstance(s, str) for s in contract["lifecycle_statuses"])
    
    assert "allowed_actions" in contract
    assert len(contract["allowed_actions"]) > 0
    assert all(isinstance(a, str) for a in contract["allowed_actions"])
    
    assert "forbidden_actions" in contract
    assert len(contract["forbidden_actions"]) > 0
    assert all(isinstance(a, str) for a in contract["forbidden_actions"])
    
    assert "required_evidence" in contract
    assert len(contract["required_evidence"]) > 0
    assert all(isinstance(e, str) for e in contract["required_evidence"])
    
    assert "next_maturity_gap" in contract
    assert isinstance(contract["next_maturity_gap"], str)


# ===== TEST GROUP 5: SAFETY FLAGS VALIDATION =====

@pytest.mark.parametrize("module_import,module_name", [
    ("app.modules.staff_recruitment.service", "get_staff_recruitment_foundation_contract"),
    ("app.modules.staff_onboarding.service", "get_staff_onboarding_foundation_contract"),
    ("app.modules.employee_records.service", "get_employee_records_foundation_contract"),
    ("app.modules.document_workflow.service", "get_document_workflow_foundation_contract"),
    ("app.modules.order_decree_registry.service", "get_order_decree_registry_foundation_contract"),
    ("app.modules.curriculum_mapping.service", "get_curriculum_mapping_foundation_contract"),
    ("app.modules.syllabus_management.service", "get_syllabus_management_foundation_contract"),
    ("app.modules.international_office.service", "get_international_office_foundation_contract"),
    ("app.modules.program_learning_outcomes.service", "get_program_learning_outcomes_foundation_contract"),
    ("app.modules.course_learning_outcomes.service", "get_course_learning_outcomes_foundation_contract"),
    ("app.modules.committee_decision_registry.service", "get_committee_decision_registry_foundation_contract"),
])
def test_safety_flags_validation(module_import, module_name):
    """Verify safety flags are all TRUE for no-claim boundaries."""
    import importlib
    mod = importlib.import_module(module_import)
    func = getattr(mod, module_name)
    
    contract = func(1)
    flags = contract["safety_flags"]
    
    # All safety flags must be True
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_live_integration_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_kpi_claim"] is True
    assert flags["no_brain_claim"] is True
    assert flags["no_autonomous_execution"] is True
    assert flags["no_external_side_effects"] is True
    assert flags["no_l3_claim"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True


# ===== TEST GROUP 6: DETERMINISM VALIDATION =====

@pytest.mark.parametrize("module_import,module_name", [
    ("app.modules.staff_recruitment.service", "get_staff_recruitment_foundation_contract"),
    ("app.modules.staff_onboarding.service", "get_staff_onboarding_foundation_contract"),
    ("app.modules.employee_records.service", "get_employee_records_foundation_contract"),
    ("app.modules.document_workflow.service", "get_document_workflow_foundation_contract"),
    ("app.modules.order_decree_registry.service", "get_order_decree_registry_foundation_contract"),
    ("app.modules.curriculum_mapping.service", "get_curriculum_mapping_foundation_contract"),
    ("app.modules.syllabus_management.service", "get_syllabus_management_foundation_contract"),
    ("app.modules.international_office.service", "get_international_office_foundation_contract"),
    ("app.modules.program_learning_outcomes.service", "get_program_learning_outcomes_foundation_contract"),
    ("app.modules.course_learning_outcomes.service", "get_course_learning_outcomes_foundation_contract"),
    ("app.modules.committee_decision_registry.service", "get_committee_decision_registry_foundation_contract"),
])
def test_determinism_identical_input_identical_output(module_import, module_name):
    """Verify determinism: identical inputs always return identical outputs."""
    import importlib
    mod = importlib.import_module(module_import)
    func = getattr(mod, module_name)
    
    contract1 = func(1)
    contract2 = func(1)
    
    # Contracts should be structurally identical
    assert contract1 == contract2


# ===== TEST GROUP 7: ANTI-INFLATION VALIDATION =====

def test_no_router_required():
    """Verify no routers are created for A-027.2 modules."""
    import os
    
    modules = [
        "staff_recruitment", "staff_onboarding", "employee_records",
        "document_workflow", "order_decree_registry", "curriculum_mapping",
        "syllabus_management", "international_office", "program_learning_outcomes",
        "course_learning_outcomes", "committee_decision_registry"
    ]
    
    for module_name in modules:
        router_path = f"/home/sbs/AI/backend/app/modules/{module_name}/router.py"
        assert not os.path.exists(router_path), f"Router should not exist for {module_name}"


def test_no_schemas_required():
    """Verify no schemas are created for A-027.2 modules."""
    import os
    
    modules = [
        "staff_recruitment", "staff_onboarding", "employee_records",
        "document_workflow", "order_decree_registry", "curriculum_mapping",
        "syllabus_management", "international_office", "program_learning_outcomes",
        "course_learning_outcomes", "committee_decision_registry"
    ]
    
    for module_name in modules:
        schemas_path = f"/home/sbs/AI/backend/app/modules/{module_name}/schemas.py"
        assert not os.path.exists(schemas_path), f"Schemas should not exist for {module_name}"


def test_no_db_migrations():
    """Verify no DB migrations are required for A-027.2 foundation."""
    import os
    
    migrations_dir = "/home/sbs/AI/backend/app/db/migrations"
    
    # Count existing migrations
    if os.path.exists(migrations_dir):
        migration_files = [f for f in os.listdir(migrations_dir) if f.startswith("a0272")]
        assert len(migration_files) == 0, "A-027.2 should not create DB migrations"
