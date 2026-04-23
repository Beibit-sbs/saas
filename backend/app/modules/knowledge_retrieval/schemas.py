"""Phase XII-XII2: Knowledge Retrieval schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DocumentIngestRequestSchema(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1, max_length=50_000)
    doc_type: Literal["policy", "guideline", "syllabus", "research", "general"] = "general"
    source_ref: str | None = Field(default=None, max_length=512)
    tags: list[str] = Field(default_factory=list)


class DocumentIngestResponseSchema(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    status: str
    chunk_count: int


class SemanticSearchRequestSchema(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    doc_type: Literal["policy", "guideline", "syllabus", "research", "general"] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItemSchema(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    excerpt: str
    score: float
    source_ref: str | None


class SemanticSearchResponseSchema(BaseModel):
    query: str
    results: list[SearchResultItemSchema]
    total_found: int


class KnowledgeBaseStatsSchema(BaseModel):
    total_documents: int
    total_chunks: int
    doc_type_breakdown: dict[str, int]
    last_ingest_at: str | None
