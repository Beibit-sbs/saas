"""Phase XII-XII2: Knowledge Retrieval router tests."""
from __future__ import annotations

import pytest

from app.core.db import get_raw_conn
from app.modules.auth.token_service import create_access_token
from tests.conftest import client

BASE = "/api/admin/knowledge-retrieval"

HEADERS = {
    "Authorization": (
        "Bearer "
        + create_access_token(
            user_id="kr@example.com",
            roles=["admin"],
            auth_source="test",
            tenant_id=1,
            permissions=["knowledge_retrieval.read", "knowledge_retrieval.write"],
        )
    )
}


def _headers_for_tenant(tenant_id: int) -> dict[str, str]:
    return {
        "Authorization": (
            "Bearer "
            + create_access_token(
                user_id=f"kr-tenant-{tenant_id}@example.com",
                roles=["admin"],
                auth_source="test",
                tenant_id=tenant_id,
                permissions=["knowledge_retrieval.read", "knowledge_retrieval.write"],
            )
        )
    }


@pytest.fixture(autouse=True)
def _cleanup_knowledge_docs() -> None:
    with get_raw_conn() as conn:
        if conn is None:
            pytest.skip("DATABASE_URL is required for knowledge_retrieval integration tests")
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM university_knowledge_documents WHERE tenant_id IN (1, 2)"
            )
        conn.commit()

    yield

    with get_raw_conn() as conn:
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM university_knowledge_documents WHERE tenant_id IN (1, 2)"
            )
        conn.commit()


def test_health_ok() -> None:
    response = client.get(f"{BASE}/health", headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["module"] == "knowledge_retrieval"


def test_ingest_document() -> None:
    payload = {
        "title": "University Thesis Policy 2026",
        "content": "The thesis must be submitted within 6 months of defense approval. "
                   "Extensions require dean sign-off. Plagiarism results in immediate rejection.",
        "doc_type": "policy",
        "source_ref": "policy/thesis-2026",
    }
    response = client.post(f"{BASE}/ingest", headers=HEADERS, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["doc_id"]
    assert body["status"] == "indexed"
    assert body["chunk_count"] >= 1


def test_semantic_search() -> None:
    # Ingest first
    client.post(
        f"{BASE}/ingest",
        headers=HEADERS,
        json={
            "title": "Academic Integrity Guidelines",
            "content": "Students must not plagiarise. AI-generated content requires disclosure. "
                       "Violations are reviewed by the integrity committee.",
            "doc_type": "guideline",
        },
    )
    response = client.post(
        f"{BASE}/search",
        headers=HEADERS,
        json={"query": "plagiarism policy", "top_k": 5},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "results" in body
    assert isinstance(body["results"], list)
    assert body["total_found"] >= 0


def test_stats_endpoint() -> None:
    response = client.get(f"{BASE}/stats", headers=HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "total_documents" in body
    assert "total_chunks" in body
    assert "doc_type_breakdown" in body


def test_ingest_search_and_stats_are_db_backed() -> None:
    ingest_a = client.post(
        f"{BASE}/ingest",
        headers=HEADERS,
        json={
            "title": "Academic Integrity Policy",
            "content": "Plagiarism is prohibited. Violations lead to disciplinary action.",
            "doc_type": "policy",
            "source_ref": "policy/integrity",
            "tags": ["integrity", "discipline"],
        },
    )
    assert ingest_a.status_code == 200, ingest_a.text
    doc_a = ingest_a.json()["doc_id"]

    ingest_b = client.post(
        f"{BASE}/ingest",
        headers=HEADERS,
        json={
            "title": "Library Research Guide",
            "content": "Use peer-reviewed databases for literature review and citation quality.",
            "doc_type": "guideline",
            "source_ref": "guide/library-research",
        },
    )
    assert ingest_b.status_code == 200, ingest_b.text

    search = client.post(
        f"{BASE}/search",
        headers=HEADERS,
        json={"query": "plagiarism disciplinary policy", "top_k": 5},
    )
    assert search.status_code == 200, search.text
    payload = search.json()
    assert payload["total_found"] >= 1
    assert any(item["doc_id"] == doc_a for item in payload["results"])

    stats = client.get(f"{BASE}/stats", headers=HEADERS)
    assert stats.status_code == 200, stats.text
    stats_body = stats.json()
    assert stats_body["total_documents"] == 2
    assert stats_body["doc_type_breakdown"].get("policy") == 1
    assert stats_body["doc_type_breakdown"].get("guideline") == 1

    with get_raw_conn() as conn:
        assert conn is not None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM university_knowledge_documents WHERE tenant_id = %s",
                (1,),
            )
            count = int(cur.fetchone()[0])
    assert count == 2


def test_search_doc_type_filter_uses_stored_documents() -> None:
    client.post(
        f"{BASE}/ingest",
        headers=HEADERS,
        json={
            "title": "General Academic Guide",
            "content": "General study planning and exam preparation tips.",
            "doc_type": "general",
        },
    )
    policy_ingest = client.post(
        f"{BASE}/ingest",
        headers=HEADERS,
        json={
            "title": "Exam Policy",
            "content": "Exam policy defines invigilation and violation handling.",
            "doc_type": "policy",
        },
    )
    assert policy_ingest.status_code == 200, policy_ingest.text
    policy_doc_id = policy_ingest.json()["doc_id"]

    filtered = client.post(
        f"{BASE}/search",
        headers=HEADERS,
        json={"query": "exam policy", "doc_type": "policy", "top_k": 10},
    )
    assert filtered.status_code == 200, filtered.text
    body = filtered.json()
    assert body["total_found"] >= 1
    assert all(item["doc_type"] == "policy" for item in body["results"])
    assert any(item["doc_id"] == policy_doc_id for item in body["results"])


def test_tenant_isolation_for_ingest_and_search() -> None:
    headers_tenant_1 = _headers_for_tenant(1)
    headers_tenant_2 = _headers_for_tenant(2)

    t1_ingest = client.post(
        f"{BASE}/ingest",
        headers=headers_tenant_1,
        json={
            "title": "Tenant1 Confidential Policy",
            "content": "Tenant one only policy content.",
            "doc_type": "policy",
        },
    )
    assert t1_ingest.status_code == 200, t1_ingest.text

    t2_ingest = client.post(
        f"{BASE}/ingest",
        headers=headers_tenant_2,
        json={
            "title": "Tenant2 Confidential Policy",
            "content": "Tenant two only policy content.",
            "doc_type": "policy",
        },
    )
    assert t2_ingest.status_code == 200, t2_ingest.text

    search_t1 = client.post(
        f"{BASE}/search",
        headers=headers_tenant_1,
        json={"query": "tenant two only", "top_k": 5},
    )
    assert search_t1.status_code == 200, search_t1.text
    assert search_t1.json()["total_found"] == 0

    search_t2 = client.post(
        f"{BASE}/search",
        headers=headers_tenant_2,
        json={"query": "tenant one only", "top_k": 5},
    )
    assert search_t2.status_code == 200, search_t2.text
    assert search_t2.json()["total_found"] == 0
