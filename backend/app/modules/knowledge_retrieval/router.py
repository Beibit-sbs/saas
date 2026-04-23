"""Phase XII-XII2: Knowledge Retrieval router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.knowledge_retrieval.schemas import (
    DocumentIngestRequestSchema,
    DocumentIngestResponseSchema,
    KnowledgeBaseStatsSchema,
    SemanticSearchRequestSchema,
    SemanticSearchResponseSchema,
)
from app.modules.knowledge_retrieval.service import (
    get_knowledge_base_stats,
    ingest_document,
    semantic_search,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/knowledge-retrieval", tags=["knowledge-retrieval"])


@router.get("/health")
def health_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("knowledge_retrieval.read"))],
) -> dict[str, str]:
    return {"status": "ok", "module": "knowledge_retrieval", "phase": "xii2"}


@router.post("/ingest", response_model=DocumentIngestResponseSchema)
def ingest_endpoint(
    payload: DocumentIngestRequestSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("knowledge_retrieval.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> DocumentIngestResponseSchema:
    return ingest_document(
        tenant_id=int(tenant["id"]),
        actor_id=actor,
        payload=payload,
    )


@router.post("/search", response_model=SemanticSearchResponseSchema)
def search_endpoint(
    payload: SemanticSearchRequestSchema,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("knowledge_retrieval.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> SemanticSearchResponseSchema:
    return semantic_search(
        tenant_id=int(tenant["id"]),
        payload=payload,
    )


@router.get("/stats", response_model=KnowledgeBaseStatsSchema)
def stats_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("knowledge_retrieval.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> KnowledgeBaseStatsSchema:
    return get_knowledge_base_stats(tenant_id=int(tenant["id"]))
