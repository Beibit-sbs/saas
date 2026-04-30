from __future__ import annotations

from tests.conftest import client


def _openapi_paths() -> dict[str, dict[str, object]]:
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    schema = response.json()
    paths = schema.get("paths")
    assert isinstance(paths, dict)
    return paths


def test_faculty_workload_frontend_contract_paths_exist() -> None:
    """Blocker #16/#17 guardrail: frontend workload hooks must map to real backend routes."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/org/faculty/{faculty_id}/workload"),
        ("GET", "/api/admin/org/faculty/workload/alerts"),
        ("GET", "/api/admin/org/faculty/workload/department/{department}"),
        ("GET", "/api/admin/org/faculty/workload/metrics"),
        ("GET", "/api/admin/org/faculty/{faculty_id}/capacity"),
        ("PUT", "/api/admin/org/faculty/{faculty_id}/capacity"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_teaching_quality_frontend_contract_paths_exist() -> None:
    """Blocker #16/#17 guardrail: teaching-quality hooks must map to real backend routes."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/teaching-quality/faculty/{faculty_id}/kpi"),
        ("GET", "/api/admin/teaching-quality/dashboard/{department}"),
        ("GET", "/api/admin/teaching-quality/benchmarks"),
        ("GET", "/api/admin/teaching-quality/report"),
        ("GET", "/api/admin/teaching-quality/faculty/{faculty_id}/improvements"),
        ("POST", "/api/admin/teaching-quality/faculty/{faculty_id}/metric"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_governance_frontend_contract_paths_exist() -> None:
    """Regression guardrail for previously orphaned governance pages."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/syllabus-governance"),
        ("POST", "/api/admin/syllabus-governance"),
        ("GET", "/api/admin/syllabus-governance/dashboard/summary"),
        ("GET", "/api/admin/exam-governance"),
        ("POST", "/api/admin/exam-governance"),
        ("GET", "/api/admin/exam-governance/dashboard/summary"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_admissions_frontend_contract_core_paths_exist() -> None:
    """Blocker #16 guardrail for admissions hooks core route set."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/admissions/applicants"),
        ("POST", "/api/admin/admissions/applicants"),
        ("GET", "/api/admin/admissions/applicants/{applicant_id}"),
        ("PATCH", "/api/admin/admissions/applicants/{applicant_id}"),
        ("GET", "/api/admin/admissions/applications"),
        ("POST", "/api/admin/admissions/applications"),
        ("GET", "/api/admin/admissions/applications/{application_id}"),
        ("POST", "/api/admin/admissions/applications/{application_id}/submit"),
        ("POST", "/api/admin/admissions/applications/{application_id}/stage-transition"),
        ("POST", "/api/admin/admissions/applications/{application_id}/decision"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_interventions_frontend_contract_paths_exist() -> None:
    """Blocker #16 guardrail for interventions hooks route set."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/interventions/cases"),
        ("POST", "/api/admin/interventions/cases"),
        ("GET", "/api/admin/interventions/cases/{case_id}"),
        ("GET", "/api/admin/interventions/cases/{case_id}/actions"),
        ("POST", "/api/admin/interventions/cases/{case_id}/actions"),
        ("POST", "/api/admin/interventions/cases/{case_id}/take"),
        ("POST", "/api/admin/interventions/cases/{case_id}/assign"),
        ("POST", "/api/admin/interventions/cases/{case_id}/status"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_org_units_frontend_contract_paths_exist() -> None:
    """Blocker #16 guardrail for org-units hooks route set."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/org-units"),
        ("POST", "/api/admin/org-units"),
        ("GET", "/api/admin/org-units/tree"),
        ("PATCH", "/api/admin/org-units/{unit_id}"),
        ("DELETE", "/api/admin/org-units/{unit_id}"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_academic_records_frontend_contract_paths_exist() -> None:
    """Blocker #16 guardrail for academic-records hooks route set."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/university/records"),
        ("POST", "/api/admin/university/records"),
        ("PUT", "/api/admin/university/records/{record_id}"),
        ("DELETE", "/api/admin/university/records/{record_id}"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_audit_frontend_contract_paths_exist() -> None:
    """Blocker #16 guardrail for audit hooks route set."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/audit/events"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_scheduling_existing_frontend_contract_paths_exist() -> None:
    """Blocker #16 guardrail for scheduling/risk hooks paths that currently exist in backend."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("POST", "/api/admin/scheduling/sections"),
        ("GET", "/api/admin/scheduling/sections/{section_id}/lessons"),
        ("GET", "/api/admin/scheduling/sections/{section_id}/attendance-trends"),
        ("GET", "/api/admin/scheduling/lessons/{lesson_instance_id}/attendance"),
        ("PUT", "/api/admin/scheduling/lessons/{lesson_instance_id}/attendance"),
        ("GET", "/api/admin/interventions/risk/students/{student_profile_id}/latest"),
        ("GET", "/api/admin/interventions/risk/students/{student_profile_id}/history"),
        ("GET", "/api/admin/interventions/risk/kpi-summary"),
    ]

    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_scheduling_section_detail_update_contract_paths_exist() -> None:
    """Blocker #16: GET /sections/{id} and PATCH /sections/{id} required by frontend api.ts."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/scheduling/sections/{section_id}"),
        ("PATCH", "/api/admin/scheduling/sections/{section_id}"),
    ]
    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"


def test_procurement_contracts_api_prefix_contract() -> None:
    """Blocker #15: contracts frontend uses /api/admin/procurement/contracts prefix."""
    paths = _openapi_paths()
    expected: list[tuple[str, str]] = [
        ("GET", "/api/admin/procurement/contracts"),
        ("POST", "/api/admin/procurement/contracts"),
    ]
    for method, path in expected:
        assert path in paths, f"Missing backend route for frontend contract: {path}"
        assert method.lower() in paths[path], f"Missing {method} on route: {path}"
