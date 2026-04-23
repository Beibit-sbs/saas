"""Phase XII-XII2: Knowledge Retrieval router tests."""
from __future__ import annotations

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
