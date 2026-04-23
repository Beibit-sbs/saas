"""Phase I4 hardening — Tenant-isolation regression pack.

Covers:
  I4.1 — fail-closed: no tenant context → 401 on all protected endpoints
  I4.2 — fail-closed: invalid/zero tenant in token → 401/403
  I4.3 — cross-tenant read prohibition: tenant A cannot read tenant B data via header
  I4.4 — data leakage negative tests: data created by tenant A absent from tenant B responses
  I4.5 — memory-layer isolation: list_entities_for_tenant_impl filters by tenant_id
  I4.6 — university core entities isolated across tenants
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import pytest

from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.tenants.provisioning_service import TenantProvisioningService


pytestmark = pytest.mark.security_regression


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _mint_token(*, include_tid: bool, tid_value: int | None = None, roles: list[str] | None = None) -> str:
    """Mint a JWT token with optional tenant_id for fail-closed tests."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, object] = {
        "sub": "i4.regression.user",
        "roles": roles or ["admin"],
        "scp": ["admin.read", "admin.write"],
        "src": "test",
        "jti": str(uuid4()),
        "pg": False,
        "iat": now,
        "exp": now + 3600,
        "token_type": "access",
        "ver": 1,
    }
    if include_tid:
        payload["tid"] = tid_value

    header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret = os.environ["JWT_SECRET"].encode()
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url(sig)}"


def _new_tenant(suffix: str) -> dict:
    """Provision a fresh tenant and return the tenant dict."""
    return TenantProvisioningService.create_tenant_with_defaults(
        tenant_name=f"i4-{suffix}",
        admin_email=f"i4-{suffix}@example.local",
        plan_code="free",
        actor="i4-tests",
    )["tenant"]


def _headers_for(tenant_id: int) -> dict[str, str]:
    return _auth_headers(f"i4-user-{tenant_id}@example.local", ["admin"], tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# I4.1 — Fail-closed: no tenant context
# ---------------------------------------------------------------------------

PROTECTED_ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/admin/students"),
    ("GET", "/api/admin/org/faculty"),
    ("GET", "/api/admin/org/programs"),
    ("GET", "/api/admin/org/courses"),
    ("GET", "/api/admin/local-users"),
    ("GET", "/api/admin/audit/events"),
    ("GET", "/api/admin/jobs"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_no_auth_fails_closed_on_protected_endpoint(method: str, path: str) -> None:
    """Unauthenticated requests must be rejected 401 (fail-closed)."""
    resp = getattr(client, method.lower())(path)
    assert resp.status_code == 401, f"{method} {path}: expected 401 got {resp.status_code}"


@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
def test_token_without_tenant_claim_fails_closed(method: str, path: str) -> None:
    """Token with no tid claim must be rejected (fail-closed)."""
    token = _mint_token(include_tid=False)
    resp = getattr(client, method.lower())(path, headers={"Authorization": f"Bearer {token}"})
    # Expect 401 — invalid/missing tenant claim
    assert resp.status_code in (401, 403), (
        f"{method} {path}: expected 401/403 got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# I4.2 — Fail-closed: invalid tenant values in token
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_tid", [0, -1, -999])
def test_zero_or_negative_tenant_id_fails_closed(bad_tid: int) -> None:
    """Token with zero/negative tenant_id must be rejected."""
    token = _mint_token(include_tid=True, tid_value=bad_tid)
    resp = client.get("/api/admin/students", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (401, 403), f"tid={bad_tid}: expected 401/403 got {resp.status_code}"


def test_missing_tenant_claim_write_fails_closed() -> None:
    """Write endpoint must also reject token without tid claim."""
    token = _mint_token(include_tid=False)
    resp = client.post(
        "/api/admin/local-users",
        headers={"Authorization": f"Bearer {token}"},
        json={"login": "blocked", "password": "Blocked!123", "display_name": "Blocked", "roles": ["admin"]},
    )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# I4.3 — Cross-tenant read prohibition via X-Tenant-ID header
# ---------------------------------------------------------------------------

def test_cross_tenant_header_override_forbidden_for_admin() -> None:
    """Admin of tenant A using X-Tenant-ID of tenant B must get 403."""
    suffix = uuid4().hex[:8]
    tenant_b = _new_tenant(f"b-{suffix}")
    tenant_b_id = int(tenant_b["id"])

    # ADMIN_HEADERS is authenticated for tenant 1 (TEST_PLATFORM_TENANT_ID)
    resp = client.get(
        "/api/admin/students",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_b_id)},
    )
    # Must be 403 (cross-tenant override forbidden) not 200
    assert resp.status_code == 403, (
        f"Expected 403 cross-tenant, got {resp.status_code}: {resp.text}"
    )


def test_cross_tenant_job_query_param_does_not_leak_data() -> None:
    """Passing another tenant's ID as query param must not leak data from that tenant."""
    suffix = uuid4().hex[:8]
    tenant_b = _new_tenant(f"b2-{suffix}")
    tenant_b_id = int(tenant_b["id"])

    # Attempt to list tenant B's jobs while authenticated as tenant A
    resp = client.get(
        f"/api/admin/jobs?tenant_id={tenant_b_id}",
        headers=ADMIN_HEADERS,
    )
    # Must not return 200 with foreign tenant data; 404 or 200 with empty list are both acceptable
    if resp.status_code == 200:
        items = resp.json()
        if isinstance(items, list):
            for item in items:
                item_tid = str(item.get("tenant_id", ""))
                assert item_tid != str(tenant_b_id), (
                    f"Data leakage: job from tenant {tenant_b_id} returned to tenant 1"
                )
        elif isinstance(items, dict):
            for item in items.get("items", []) or items.get("jobs", []):
                assert str(item.get("tenant_id", "")) != str(tenant_b_id)
    else:
        # 403, 404, etc. are all acceptable — no data leakage
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# I4.4 — Data leakage negative tests (memory-layer impl)
# University core entities are tested at impl level to avoid dependency on
# external DB in the test container; isolation guarantee is the same.
# ---------------------------------------------------------------------------

def test_student_created_by_tenant_a_not_visible_to_tenant_b() -> None:
    """A student record created under tenant A must not appear in tenant B's list."""
    from app.modules.university_core.tenant_entity_impl import (
        create_entity_for_tenant_impl,
        list_entities_for_tenant_impl,
    )

    suffix = uuid4().hex[:8]
    tid_a = 61001
    tid_b = 61002

    student_id = f"LEAK-STU-{suffix}"
    create_entity_for_tenant_impl(
        "students",
        {
            "student_id": student_id,
            "first_name": "LeakTest",
            "last_name": "Student",
            "email": f"leak-stu-{suffix}@a.local",
            "status": "active",
        },
        tid_a,
    )

    rows_b = list_entities_for_tenant_impl("students", tid_b)
    ids_b = {str(r.get("student_id")) for r in rows_b}
    assert student_id not in ids_b, (
        f"Data leakage: student {student_id} from tid={tid_a} visible to tid={tid_b}"
    )


def test_program_created_by_tenant_a_not_visible_to_tenant_b() -> None:
    """A program record created under tenant A must not appear in tenant B's list."""
    from app.modules.university_core.tenant_entity_impl import (
        create_entity_for_tenant_impl,
        list_entities_for_tenant_impl,
    )

    suffix = uuid4().hex[:8]
    tid_a = 62001
    tid_b = 62002

    program_code = f"LEAK-PROG-{suffix}"
    create_entity_for_tenant_impl(
        "programs",
        {
            "program_code": program_code,
            "title": "Leak Program",
            "degree_type": "bachelor",
            "faculty": "test",
            "status": "active",
        },
        tid_a,
    )

    rows_b = list_entities_for_tenant_impl("programs", tid_b)
    codes_b = {str(r.get("program_code")) for r in rows_b}
    assert program_code not in codes_b, (
        f"Data leakage: program {program_code} from tid={tid_a} visible to tid={tid_b}"
    )


def test_faculty_created_by_tenant_a_not_visible_to_tenant_b() -> None:
    """Faculty records must be isolated per tenant."""
    from app.modules.university_core.tenant_entity_impl import (
        create_entity_for_tenant_impl,
        list_entities_for_tenant_impl,
    )

    suffix = uuid4().hex[:8]
    tid_a = 63001
    tid_b = 63002

    faculty_id = f"LEAK-FAC-{suffix}"
    create_entity_for_tenant_impl(
        "faculty",
        {
            "faculty_id": faculty_id,
            "first_name": "LeakFac",
            "last_name": "Test",
            "department": "CS",
            "email": f"leakfac-{suffix}@a.local",
            "status": "active",
        },
        tid_a,
    )

    rows_b = list_entities_for_tenant_impl("faculty", tid_b)
    ids_b = {str(r.get("faculty_id")) for r in rows_b}
    assert faculty_id not in ids_b, (
        f"Data leakage: faculty {faculty_id} from tid={tid_a} visible to tid={tid_b}"
    )


# ---------------------------------------------------------------------------
# I4.5 — Memory-layer isolation: list_entities_for_tenant_impl
# ---------------------------------------------------------------------------

def test_memory_layer_list_filters_by_tenant_id() -> None:
    """list_entities_for_tenant_impl returns only rows matching tenant_id."""
    from app.modules.university_core.shared import _state, _state_lock, ENTITY_CONFIGS

    entity = "students"
    assert entity in ENTITY_CONFIGS

    with _state_lock:
        # Inject two records for different tenants
        _state.data[entity][99901] = {
            "id": 99901,
            "student_id": "MEM-STU-A",
            "first_name": "Mem",
            "last_name": "A",
            "email": "mem-a@x.local",
            "status": "active",
            "tenant_id": "9001",
            "created_at": "2026-01-01T00:00:00",
        }
        _state.data[entity][99902] = {
            "id": 99902,
            "student_id": "MEM-STU-B",
            "first_name": "Mem",
            "last_name": "B",
            "email": "mem-b@x.local",
            "status": "active",
            "tenant_id": "9002",
            "created_at": "2026-01-01T00:00:00",
        }

    from app.modules.university_core.tenant_entity_impl import list_entities_for_tenant_impl

    rows_9001 = list_entities_for_tenant_impl(entity, 9001)
    rows_9002 = list_entities_for_tenant_impl(entity, 9002)

    # Cleanup
    with _state_lock:
        _state.data[entity].pop(99901, None)
        _state.data[entity].pop(99902, None)

    ids_9001 = {str(r.get("student_id")) for r in rows_9001}
    ids_9002 = {str(r.get("student_id")) for r in rows_9002}

    assert "MEM-STU-A" in ids_9001
    assert "MEM-STU-B" not in ids_9001
    assert "MEM-STU-B" in ids_9002
    assert "MEM-STU-A" not in ids_9002


def test_memory_layer_update_blocked_for_wrong_tenant() -> None:
    """_update_entity_for_tenant_memory_impl raises ValueError for wrong tenant."""
    from app.modules.university_core.shared import _state, _state_lock, ENTITY_CONFIGS
    from app.modules.university_core.tenant_entity_impl import _update_entity_for_tenant_memory_impl

    entity = "students"
    fields = ENTITY_CONFIGS[entity].fields

    with _state_lock:
        _state.data[entity][88801] = {
            "id": 88801,
            "student_id": "UPD-STU-A",
            "first_name": "Upd",
            "last_name": "A",
            "email": "upd-a@x.local",
            "status": "active",
            "tenant_id": "8801",
            "created_at": "2026-01-01T00:00:00",
        }

    payload = {f: "x" for f in fields if f != "tenant_id"}
    payload["tenant_id"] = "8801"
    payload["student_id"] = "UPD-STU-A"
    payload["status"] = "active"
    payload["first_name"] = "Upd"
    payload["last_name"] = "A"
    payload["email"] = "upd-a@x.local"

    # Attempt update as wrong tenant
    with pytest.raises(ValueError, match="not found"):
        _update_entity_for_tenant_memory_impl(entity, 88801, payload, 9999)

    # Cleanup
    with _state_lock:
        _state.data[entity].pop(88801, None)


def test_memory_layer_delete_blocked_for_wrong_tenant() -> None:
    """_delete_entity_for_tenant_memory_impl raises ValueError for wrong tenant."""
    from app.modules.university_core.shared import _state, _state_lock
    from app.modules.university_core.tenant_entity_impl import _delete_entity_for_tenant_memory_impl

    entity = "students"
    with _state_lock:
        _state.data[entity][77701] = {
            "id": 77701,
            "student_id": "DEL-STU-A",
            "first_name": "Del",
            "last_name": "A",
            "email": "del-a@x.local",
            "status": "active",
            "tenant_id": "7701",
            "created_at": "2026-01-01T00:00:00",
        }

    with pytest.raises(ValueError, match="not found"):
        _delete_entity_for_tenant_memory_impl(entity, 77701, 9998)

    # Cleanup
    with _state_lock:
        _state.data[entity].pop(77701, None)


# ---------------------------------------------------------------------------
# I4.6 — Unknown entity rejected (prevents data-map probing attacks)
# ---------------------------------------------------------------------------

def test_unknown_entity_raises_value_error() -> None:
    """list_entities_for_tenant_impl raises ValueError for unknown entity names."""
    from app.modules.university_core.tenant_entity_impl import list_entities_for_tenant_impl

    with pytest.raises(ValueError, match="unknown entity"):
        list_entities_for_tenant_impl("__injection_attempt__", 1)


def test_unknown_entity_update_raises() -> None:
    """update_entity_for_tenant raises ValueError for unknown entity names."""
    from app.modules.university_core.tenant_entity_api import update_entity_for_tenant

    with pytest.raises((ValueError, KeyError)):
        update_entity_for_tenant("__probe__", 1, {"field": "value"}, 1)


# ---------------------------------------------------------------------------
# I4.7 — Audit events tenant-scoped
# ---------------------------------------------------------------------------

def test_audit_events_scoped_to_tenant() -> None:
    """Audit events must only return records for the requesting tenant."""
    # Any audit events created under ADMIN_HEADERS (tenant=1) must not appear
    # in a listing for a different tenant.
    suffix = uuid4().hex[:8]
    tenant_b = _new_tenant(f"aud-b-{suffix}")
    tid_b = int(tenant_b["id"])
    headers_b = _headers_for(tid_b)

    # Trigger audit event in tenant 1
    client.get("/api/admin/students", headers=ADMIN_HEADERS)

    # Tenant B should not see tenant 1's audit events
    audit_b = client.get("/api/admin/audit/events", headers=headers_b)
    assert audit_b.status_code == 200
    events = audit_b.json().get("events", [])
    for ev in events:
        ev_tid = str(ev.get("tenant_id", ""))
        assert ev_tid == str(tid_b) or ev_tid == "", (
            f"Audit leakage: event tenant_id={ev_tid} visible to tenant {tid_b}"
        )
