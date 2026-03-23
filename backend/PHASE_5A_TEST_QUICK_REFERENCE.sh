"""
Phase 5A Test Quick Reference Card

Fast lookup for most common test commands
"""

# ==============================================================================
# DIRECTORY & FILE SETUP
# ==============================================================================

cd /home/sbs/AI/backend

# Verify test file exists and compiles
python -m py_compile tests/modules/admissions/test_workflow_integration_phase_5a.py
python -m py_compile tests/modules/admissions/conftest.py

# ==============================================================================
# TEST DISCOVERY
# ==============================================================================

# List all test names
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --collect-only -q

# Count total tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --collect-only | grep "test_" | wc -l

# ==============================================================================
# BASIC EXECUTION
# ==============================================================================

# RUN ALL TESTS (19 total)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v

# Run with full output (print statements visible)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v -s

# Run with detailed traceback on failure
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -vv --tb=short

# Run with very detailed output
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -vv --tb=long

# ==============================================================================
# RUN SPECIFIC TEST CLASS
# ==============================================================================

# Happy path tests (ApplicationService.submit_application)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestSubmitApplicationHappyPath -v

# Error handling tests (ApplicationService.submit_application)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestSubmitApplicationErrors -v

# Idempotency tests (ApplicationService.submit_application)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestSubmitApplicationIdempotency -v

# Happy path tests (DecisionService.finalize_workflow_decision)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestFinalizeDecisionHappyPath -v

# Error handling tests (DecisionService.finalize_workflow_decision)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestFinalizeDecisionErrors -v

# Idempotency tests (DecisionService.finalize_workflow_decision)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestFinalizeDecisionIdempotency -v

# Tenant isolation tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestTenantIsolation -v

# Metadata JSON safety tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestMetadataJSONSafety -v

# Workflow service integration tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestStartAdmissionsWorkflowIntegration -v

# ==============================================================================
# RUN SPECIFIC TEST METHOD
# ==============================================================================

pytest tests/modules/admissions/test_workflow_integration_phase_5a.py::TestSubmitApplicationHappyPath::test_submit_application_transitions_stage_and_starts_workflow -v

# ==============================================================================
# FILTERED EXECUTION
# ==============================================================================

# Only idempotency tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -k "idempotent" -v

# Only cross-tenant tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -k "cross_tenant" -v

# Only error tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -k "Errors" -v

# Only happy path tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -k "HappyPath" -v

# ==============================================================================
# CODE COVERAGE
# ==============================================================================

# Generate coverage report (terminal)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-report=term-missing

# Generate coverage report (HTML) - opens in browser
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-report=html
open htmlcov/index.html

# Enforce minimum coverage threshold (90%)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-fail-under=90

# Enforce minimum coverage threshold (95%)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-fail-under=95

# ==============================================================================
# ASYNC/DEBUG MODES
# ==============================================================================

# Strict asyncio mode (best practice)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --asyncio-mode=strict

# Debug mode (interactive, stops on first failure)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --pdb

# Debug with print statements
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -vv -s --tb=long

# ==============================================================================
# STRESS TESTING
# ==============================================================================

# Run tests 5 times (check for flakiness)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --count=5

# Run tests 10 times
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --count=10

# ==============================================================================
# CI/CD PIPELINE COMMANDS
# ==============================================================================

# Stage 1: Syntax validation
python -m py_compile tests/modules/admissions/test_workflow_integration_phase_5a.py

# Stage 2: Execute all tests
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --asyncio-mode=strict

# Stage 3: Verify coverage >= 95%
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-fail-under=95

# Complete pipeline (all 3 stages)
python -m py_compile tests/modules/admissions/test_workflow_integration_phase_5a.py && \
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --asyncio-mode=strict && \
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-fail-under=95

# ==============================================================================
# DOCUMENTATION REFERENCE
# ==============================================================================

# View test architecture
less PHASE_5A_TEST_ARCHITECTURE.md

# View validation commands (this file)
less PHASE_5A_TEST_VALIDATION_COMMANDS.md

# View test case matrix
less PHASE_5A_TEST_CASE_MATRIX.md

# View complete summary
less PHASE_5A_TEST_SUITE_SUMMARY.md

# ==============================================================================
# TROUBLESHOOTING
# ==============================================================================

# If tests not found, verify correct directory
pwd
# Should output: /home/sbs/AI/backend

# If module not found error, verify Python path
python -c "import sys; print(sys.path)"

# If fixture not found, verify conftest.py in same directory
ls -la tests/modules/admissions/conftest.py

# View available fixtures
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --fixtures | grep "application_factory\|audit_calls\|mock_db"

# ==============================================================================
# ONE-LINER PRODUCTION VALIDATION
# ==============================================================================

# Comprehensive validation (syntax + all tests + coverage >= 95%)
python -m py_compile tests/modules/admissions/test_workflow_integration_phase_5a.py && \
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --asyncio-mode=strict --tb=short && \
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py --cov=app.modules.admissions.service --cov-fail-under=95

# Expected output:
# ✓ Syntax check passed
# ✓ 19 passed
# ✓ 95% code coverage achieved

# ==============================================================================
# EXPECTED TEST RESULTS
# ==============================================================================

"""
✓ TestSubmitApplicationHappyPath::test_submit_application_transitions_stage_and_starts_workflow PASSED
✓ TestSubmitApplicationHappyPath::test_metadata_json_safely_merged_not_overwritten PASSED
✓ TestSubmitApplicationErrors::test_submit_application_rejects_non_new_stage PASSED
✓ TestSubmitApplicationErrors::test_submit_application_rejects_version_mismatch PASSED
✓ TestSubmitApplicationErrors::test_submit_application_not_found PASSED
✓ TestSubmitApplicationErrors::test_submit_application_cross_tenant_blocked PASSED
✓ TestSubmitApplicationIdempotency::test_submit_application_idempotent_when_workflow_already_exists PASSED
✓ TestFinalizeDecisionHappyPath::test_finalize_workflow_decision_creates_decision_and_updates_application PASSED
✓ TestFinalizeDecisionHappyPath::test_finalize_workflow_decision_rejects_approval_action_mapping PASSED
✓ TestFinalizeDecisionErrors::test_finalize_workflow_decision_rejects_workflow_mismatch PASSED
✓ TestFinalizeDecisionErrors::test_finalize_workflow_decision_rejects_invalid_approval_action PASSED
✓ TestFinalizeDecisionErrors::test_finalize_workflow_decision_application_not_found PASSED
✓ TestFinalizeDecisionIdempotency::test_finalize_workflow_decision_idempotent_if_decision_exists PASSED
✓ TestTenantIsolation::test_submit_application_cross_tenant_blocked PASSED
✓ TestTenantIsolation::test_finalize_workflow_decision_cross_tenant_blocked PASSED
✓ TestMetadataJSONSafety::test_metadata_json_preserves_existing_fields PASSED
✓ TestMetadataJSONSafety::test_metadata_json_updated_safely_on_decision PASSED
✓ TestStartAdmissionsWorkflowIntegration::test_start_admissions_workflow_calls_workflow_service PASSED

======================== 19 passed in X.XXXs ========================
======================== 95%+ code coverage achieved ========================
"""

# ==============================================================================
# TIPS & TRICKS
# ==============================================================================

# View only failures (useful when many tests run)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --tb=short --lf

# Export test results to JSON
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --json-report

# Watch for file changes and re-run tests (requires pytest-watch)
ptw tests/modules/admissions/test_workflow_integration_phase_5a.py -- -v

# Run tests in parallel (requires pytest-xdist)
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v -n 4

# Generate test report for CI/CD
pytest tests/modules/admissions/test_workflow_integration_phase_5a.py -v --junitxml=test-report.xml
"""
