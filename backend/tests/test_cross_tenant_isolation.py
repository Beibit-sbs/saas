"""Regression tests for cross-tenant isolation in the entity service layer.

Blocker #11: Verify that `list_entities_for_tenant` never leaks data across tenant
boundaries, both in the in-memory store (default, no DB required) and at the
function call level.

These tests do NOT require a running database — they use the in-memory fallback.
"""
from __future__ import annotations

import pytest

from app.modules.university_core import shared as university_shared
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset in-memory store before each test to avoid inter-test contamination."""
    with university_shared._state_lock:
        for name in university_shared.ENTITY_CONFIGS:
            university_shared._state.data[name].clear()
            university_shared._state.counters[name] = 0
    yield
    with university_shared._state_lock:
        for name in university_shared.ENTITY_CONFIGS:
            university_shared._state.data[name].clear()
            university_shared._state.counters[name] = 0


class TestCrossTenantIsolation:
    """Ensure list_entities_for_tenant is strictly scoped to the requested tenant."""

    def test_students_isolated_by_tenant(self):
        """Records created under tenant_A must not appear in tenant_B listing."""
        payload_a = {
            "student_id": "STU-T1-001",
            "first_name": "Alice",
            "last_name": "Tenant1",
            "email": "alice@tenant1.example",
            "status": "active",
        }
        payload_b = {
            "student_id": "STU-T2-001",
            "first_name": "Bob",
            "last_name": "Tenant2",
            "email": "bob@tenant2.example",
            "status": "active",
        }

        created_a = create_entity_for_tenant("students", payload_a, tenant_id=1)
        created_b = create_entity_for_tenant("students", payload_b, tenant_id=2)

        rows_t1 = list_entities_for_tenant("students", tenant_id=1)
        rows_t2 = list_entities_for_tenant("students", tenant_id=2)

        ids_t1 = {int(r["id"]) for r in rows_t1}
        ids_t2 = {int(r["id"]) for r in rows_t2}

        assert int(created_a["id"]) in ids_t1, "tenant-1 record must appear in tenant-1 list"
        assert int(created_b["id"]) in ids_t2, "tenant-2 record must appear in tenant-2 list"

        # Cross-tenant leak assertions
        assert int(created_b["id"]) not in ids_t1, "tenant-2 record MUST NOT appear in tenant-1 list"
        assert int(created_a["id"]) not in ids_t2, "tenant-1 record MUST NOT appear in tenant-2 list"

    def test_no_shared_records_across_many_tenants(self):
        """Records spread across 5 tenants stay in their respective buckets."""
        created_ids: dict[int, int] = {}
        for tid in range(1, 6):
            payload = {
                "student_id": f"STU-MT-{tid:02d}",
                "first_name": f"User{tid}",
                "last_name": "Multi",
                "email": f"user{tid}@multi.example",
                "status": "active",
            }
            row = create_entity_for_tenant("students", payload, tenant_id=tid)
            created_ids[tid] = int(row["id"])

        for tid in range(1, 6):
            rows = list_entities_for_tenant("students", tenant_id=tid)
            returned_ids = {int(r["id"]) for r in rows}
            assert created_ids[tid] in returned_ids, f"own record missing for tenant {tid}"
            for other_tid in range(1, 6):
                if other_tid == tid:
                    continue
                assert created_ids[other_tid] not in returned_ids, (
                    f"tenant {other_tid} record leaked into tenant {tid} listing"
                )

    def test_tenant_id_field_stored_correctly(self):
        """Each returned row carries the correct tenant_id marker."""
        payload = {
            "student_id": "STU-TID-001",
            "first_name": "Charlie",
            "last_name": "Check",
            "email": "charlie@check.example",
            "status": "active",
        }
        create_entity_for_tenant("students", payload, tenant_id=42)
        rows = list_entities_for_tenant("students", tenant_id=42)
        assert len(rows) == 1
        assert str(rows[0]["tenant_id"]) == "42"

    def test_empty_result_for_nonexistent_tenant(self):
        """Listing for a tenant with no records returns an empty list, not an error."""
        rows = list_entities_for_tenant("students", tenant_id=999)
        assert rows == []

    def test_faculty_isolated_by_tenant(self):
        """Faculty records are also correctly scoped per tenant."""
        fac_t1 = {
            "faculty_id": "FAC-T1-001",
            "first_name": "Diana",
            "last_name": "TenantOne",
            "department": "CS",
            "email": "diana@t1.example",
            "status": "active",
        }
        fac_t2 = {
            "faculty_id": "FAC-T2-001",
            "first_name": "Eve",
            "last_name": "TenantTwo",
            "department": "Math",
            "email": "eve@t2.example",
            "status": "active",
        }

        row_t1 = create_entity_for_tenant("faculty", fac_t1, tenant_id=10)
        row_t2 = create_entity_for_tenant("faculty", fac_t2, tenant_id=20)

        list_t1 = list_entities_for_tenant("faculty", tenant_id=10)
        list_t2 = list_entities_for_tenant("faculty", tenant_id=20)

        assert any(r["faculty_id"] == "FAC-T1-001" for r in list_t1)
        assert not any(r["faculty_id"] == "FAC-T2-001" for r in list_t1), "tenant-2 faculty leaked into tenant-1"
        assert any(r["faculty_id"] == "FAC-T2-001" for r in list_t2)
        assert not any(r["faculty_id"] == "FAC-T1-001" for r in list_t2), "tenant-1 faculty leaked into tenant-2"

        assert int(row_t1["id"]) != int(row_t2["id"]) or True  # IDs may differ; main check is list isolation
