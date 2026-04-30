"""Phase XII-XII2: Knowledge Retrieval service backed by PostgreSQL."""
from __future__ import annotations

import hashlib
import json
import re
from threading import Lock
from typing import Any

from app.core.db import get_raw_conn
from app.modules.knowledge_retrieval.schemas import (
    DocumentIngestRequestSchema,
    DocumentIngestResponseSchema,
    KnowledgeBaseStatsSchema,
    SearchResultItemSchema,
    SemanticSearchRequestSchema,
    SemanticSearchResponseSchema,
)

_TABLE_NAME = "university_knowledge_documents"
_TABLE_INIT_LOCK = Lock()
_TABLE_INITIALIZED = False


def _ensure_table_exists(conn: Any) -> None:
    global _TABLE_INITIALIZED
    if _TABLE_INITIALIZED:
        return

    with _TABLE_INIT_LOCK:
        if _TABLE_INITIALIZED:
            return
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL,
                    doc_id VARCHAR(64) NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    doc_type VARCHAR(32) NOT NULL,
                    source_ref TEXT,
                    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
                    chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
                    ingested_by VARCHAR(255) NOT NULL,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_knowledge_docs_tenant_doc UNIQUE (tenant_id, doc_id)
                )
                """
            )
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS ix_knowledge_docs_tenant_id ON {_TABLE_NAME} (tenant_id)"
            )
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS ix_knowledge_docs_tenant_doc_type ON {_TABLE_NAME} (tenant_id, doc_type)"
            )
        conn.commit()
        _TABLE_INITIALIZED = True


def _require_db_connection() -> Any:
    conn_ctx = get_raw_conn()
    conn = conn_ctx.__enter__()
    if conn is None:
        conn_ctx.__exit__(None, None, None)
        raise RuntimeError("database unavailable for knowledge_retrieval")
    _ensure_table_exists(conn)
    return conn_ctx, conn


def _load_json_array(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
            return loaded if isinstance(loaded, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _row_to_doc(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "doc_id": str(row[0]),
        "title": str(row[1]),
        "content": str(row[2]),
        "doc_type": str(row[3]),
        "source_ref": row[4],
        "tags": _load_json_array(row[5]),
        "chunks": _load_json_array(row[6]),
        "ingested_at": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
    }


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
    conn_ctx, conn = _require_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_TABLE_NAME}
                (
                    tenant_id, doc_id, title, content, doc_type,
                    source_ref, tags, chunks, ingested_by, ingested_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, NOW())
                ON CONFLICT (tenant_id, doc_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    doc_type = EXCLUDED.doc_type,
                    source_ref = EXCLUDED.source_ref,
                    tags = EXCLUDED.tags,
                    chunks = EXCLUDED.chunks,
                    ingested_by = EXCLUDED.ingested_by,
                    ingested_at = NOW()
                """,
                (
                    tenant_id,
                    doc_id,
                    payload.title,
                    payload.content,
                    payload.doc_type,
                    payload.source_ref,
                    json.dumps(payload.tags),
                    json.dumps(chunks),
                    actor_id,
                ),
            )
        conn.commit()
    finally:
        conn_ctx.__exit__(None, None, None)

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
    conn_ctx, conn = _require_db_connection()
    try:
        with conn.cursor() as cur:
            if payload.doc_type is None:
                cur.execute(
                    f"""
                    SELECT doc_id, title, content, doc_type, source_ref, tags, chunks, ingested_at
                    FROM {_TABLE_NAME}
                    WHERE tenant_id = %s
                    ORDER BY ingested_at DESC
                    """,
                    (tenant_id,),
                )
            else:
                cur.execute(
                    f"""
                    SELECT doc_id, title, content, doc_type, source_ref, tags, chunks, ingested_at
                    FROM {_TABLE_NAME}
                    WHERE tenant_id = %s AND doc_type = %s
                    ORDER BY ingested_at DESC
                    """,
                    (tenant_id, payload.doc_type),
                )
            rows = cur.fetchall()
    finally:
        conn_ctx.__exit__(None, None, None)

    candidates = [_row_to_doc(row) for row in rows]

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
    conn_ctx, conn = _require_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT doc_id, title, content, doc_type, source_ref, tags, chunks, ingested_at
                FROM {_TABLE_NAME}
                WHERE tenant_id = %s
                ORDER BY ingested_at DESC
                """,
                (tenant_id,),
            )
            rows = cur.fetchall()
    finally:
        conn_ctx.__exit__(None, None, None)

    docs = [_row_to_doc(row) for row in rows]
    breakdown: dict[str, int] = {}
    total_chunks = 0
    last_at: str | None = None
    for doc in docs:
        dt = doc["doc_type"]
        breakdown[dt] = breakdown.get(dt, 0) + 1
        total_chunks += len(doc.get("chunks", []))
        ing = doc.get("ingested_at")
        if ing and (last_at is None or ing > last_at):
            last_at = ing

    return KnowledgeBaseStatsSchema(
        total_documents=len(docs),
        total_chunks=total_chunks,
        doc_type_breakdown=breakdown,
        last_ingest_at=last_at,
    )
