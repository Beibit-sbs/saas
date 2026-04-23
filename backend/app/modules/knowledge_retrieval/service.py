"""Phase XII-XII2: Knowledge Retrieval service — RAG pipeline stub."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from app.modules.knowledge_retrieval.schemas import (
    DocumentIngestRequestSchema,
    DocumentIngestResponseSchema,
    KnowledgeBaseStatsSchema,
    SearchResultItemSchema,
    SemanticSearchRequestSchema,
    SemanticSearchResponseSchema,
)

# ---------------------------------------------------------------------------
# In-memory knowledge base (unit-testable stub; replace with vector DB in prod)
# ---------------------------------------------------------------------------
_KNOWLEDGE_BASE: dict[int, list[dict[str, Any]]] = {}  # tenant_id → documents


def _tenant_kb(tenant_id: int) -> list[dict[str, Any]]:
    return _KNOWLEDGE_BASE.setdefault(tenant_id, [])


def _chunk_text(text: str, chunk_size: int = 512) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    for i in range(0, max(len(words), 1), chunk_size // 6):  # rough word-based chunks
        chunk = " ".join(words[i : i + chunk_size // 6])
        if chunk:
            chunks.append(chunk)
    return chunks or [text[:chunk_size]]


def ingest_document(
    *,
    tenant_id: int,
    actor_id: str,
    payload: DocumentIngestRequestSchema,
) -> DocumentIngestResponseSchema:
    doc_id = hashlib.sha256(
        f"{tenant_id}:{payload.title}:{payload.content[:64]}".encode()
    ).hexdigest()[:16]

    chunks = _chunk_text(payload.content)
    doc = {
        "doc_id": doc_id,
        "tenant_id": tenant_id,
        "title": payload.title,
        "content": payload.content,
        "doc_type": payload.doc_type,
        "source_ref": payload.source_ref,
        "tags": payload.tags,
        "chunks": chunks,
        "ingested_by": actor_id,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    kb = _tenant_kb(tenant_id)
    # Replace if doc_id already exists
    kb[:] = [d for d in kb if d["doc_id"] != doc_id]
    kb.append(doc)

    return DocumentIngestResponseSchema(
        doc_id=doc_id,
        title=payload.title,
        doc_type=payload.doc_type,
        status="indexed",
        chunk_count=len(chunks),
    )


def _score(query: str, doc: dict[str, Any]) -> float:
    """Simple keyword overlap score (0–1). Replace with embeddings in prod."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text = (doc["title"] + " " + doc["content"]).lower()
    doc_tokens = set(re.findall(r"\w+", text))
    if not query_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


def semantic_search(
    *,
    tenant_id: int,
    payload: SemanticSearchRequestSchema,
) -> SemanticSearchResponseSchema:
    kb = _tenant_kb(tenant_id)
    candidates = kb if payload.doc_type is None else [d for d in kb if d["doc_type"] == payload.doc_type]

    scored = [
        (doc, _score(payload.query, doc))
        for doc in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: payload.top_k]

    results = [
        SearchResultItemSchema(
            doc_id=doc["doc_id"],
            title=doc["title"],
            doc_type=doc["doc_type"],
            excerpt=doc["content"][:300] + ("..." if len(doc["content"]) > 300 else ""),
            score=round(score, 4),
            source_ref=doc.get("source_ref"),
        )
        for doc, score in top
    ]

    return SemanticSearchResponseSchema(
        query=payload.query,
        results=results,
        total_found=len(results),
    )


def get_knowledge_base_stats(*, tenant_id: int) -> KnowledgeBaseStatsSchema:
    kb = _tenant_kb(tenant_id)
    breakdown: dict[str, int] = {}
    total_chunks = 0
    last_at: str | None = None
    for doc in kb:
        dt = doc["doc_type"]
        breakdown[dt] = breakdown.get(dt, 0) + 1
        total_chunks += len(doc.get("chunks", []))
        ing = doc.get("ingested_at")
        if ing and (last_at is None or ing > last_at):
            last_at = ing

    return KnowledgeBaseStatsSchema(
        total_documents=len(kb),
        total_chunks=total_chunks,
        doc_type_breakdown=breakdown,
        last_ingest_at=last_at,
    )
