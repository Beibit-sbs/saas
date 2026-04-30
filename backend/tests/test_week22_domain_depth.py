"""Week 22 — Domain Depth: Research Publication Cap + Review Record Side Effect.

Tests:
  W22.1 - Source guard: _PUBLICATION_STATUS_MAX_ACTIVE and _ensure_publication_review_record present
  W22.2 - Exceeding active stalled publications for an author returns 422
  W22.3 - Transitioning publication to 'submitted' auto-creates publication_review_records entry
  W22.4 - Multiple _ensure_publication_review_record calls for same publication_id are idempotent
"""
from __future__ import annotations

import inspect
import uuid

from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/research"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="week22.research@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["research.read", "research.write"],
        )
    )
}


def _reset_state() -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        for key in ("research_publications", "publication_review_records"):
            if key in university_shared._state.data:
                university_shared._state.data[key].clear()
                university_shared._state.counters[key] = 0


def setup_module(_: object) -> None:
    _reset_state()


def teardown_function(_: object) -> None:
    _reset_state()


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _seed_active_grant_for_author(lead_author_id: str) -> None:
    from app.modules.university_core import shared as university_shared

    with university_shared._state_lock:
        university_shared._state.data.setdefault("research_grants", {})
        university_shared._state.counters.setdefault("research_grants", 0)
        university_shared._state.counters["research_grants"] += 1
        gid = university_shared._state.counters["research_grants"]
        university_shared._state.data["research_grants"][gid] = {
            "id": gid,
            "grant_code": f"GRT-{_uid()}",
            "title": "Week22 Seed Grant",
            "pi_faculty_id": lead_author_id,
            "status": "active",
            "tenant_id": "1",
        }


def _create_publication(lead_author_id: str, status: str = "draft") -> dict:
    _seed_active_grant_for_author(lead_author_id)
    payload = {
        "publication_code": f"PUB-{_uid()}",
        "title": f"Test Publication {_uid()}",
        "lead_author_id": lead_author_id,
        "target_venue": "Journal of Testing",
        "last_activity_days": 5,
        "status": status,
    }
    resp = client.post(f"{BASE}/publications", headers=HEADERS, json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# W22.1 – Source guard
# ---------------------------------------------------------------------------

def test_w22_source_contains_publication_cap_and_review_helper() -> None:
    from app.modules.research import service as research_service

    src = inspect.getsource(research_service)
    assert "_PUBLICATION_STATUS_MAX_ACTIVE" in src, (
        "_PUBLICATION_STATUS_MAX_ACTIVE dict must exist in research service"
    )
    assert "_ensure_publication_review_record" in src, (
        "_ensure_publication_review_record helper must exist in research service"
    )


# ---------------------------------------------------------------------------
# W22.2 – Cap exceeded for stalled publications (max=1) → 422
# ---------------------------------------------------------------------------

def test_w22_stalled_cap_exceeded_returns_422() -> None:
    author = f"author-{_uid()}"
    # First stalled publication should succeed
    _create_publication(author, "stalled")

    # Second stalled publication must be rejected
    resp = client.post(
        f"{BASE}/publications",
        headers=HEADERS,
        json={
            "publication_code": f"PUB-{_uid()}",
            "title": "Another Stalled",
            "lead_author_id": author,
            "target_venue": "Some Journal",
            "last_activity_days": 10,
            "status": "stalled",
        },
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# W22.3 – Transition to 'submitted' auto-creates publication_review_records entry
# ---------------------------------------------------------------------------

def test_w22_transition_to_submitted_creates_review_record() -> None:
    from app.modules.university_core import shared as university_shared

    author = f"author-{_uid()}"
    data = _create_publication(author, "draft")
    pub_id = data["item"]["id"]

    resp = client.patch(
        f"{BASE}/publications/{pub_id}/status",
        headers=HEADERS,
        json={"status": "submitted"},
    )
    assert resp.status_code == 200, resp.text

    with university_shared._state_lock:
        records = list(university_shared._state.data.get("publication_review_records", {}).values())

    matched = [
        r for r in records
        if str(r.get("source_entity_id")) == str(pub_id)
        and str(r.get("integration_source")) == "research_submission"
    ]
    assert len(matched) == 1, (
        f"Expected 1 review record for pub_id={pub_id}, found {len(matched)}"
    )
    assert str(matched[0]["lead_author_id"]) == author


# ---------------------------------------------------------------------------
# W22.4 – _ensure_publication_review_record is idempotent (3 calls → 1 record)
# ---------------------------------------------------------------------------

def test_w22_ensure_publication_review_record_is_idempotent() -> None:
    from app.modules.university_core import shared as university_shared
    from app.modules.research.service import _ensure_publication_review_record

    author = f"author-{_uid()}"
    data = _create_publication(author, "draft")
    pub_id = data["item"]["id"]
    pub_data = data["item"]

    for _ in range(3):
        _ensure_publication_review_record(tenant_id=1, publication_id=pub_id, publication_data=pub_data)

    with university_shared._state_lock:
        records = list(university_shared._state.data.get("publication_review_records", {}).values())

    matched = [
        r for r in records
        if str(r.get("source_entity_id")) == str(pub_id)
        and str(r.get("integration_source")) == "research_submission"
    ]
    assert len(matched) == 1, (
        f"Idempotent helper produced {len(matched)} records, expected exactly 1"
    )
