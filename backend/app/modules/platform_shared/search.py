from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SearchQuery:
    tenant_id: int
    text: str
    module: str | None = None
    entity: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class SearchDocument:
    tenant_id: int
    module: str
    entity: str
    entity_id: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SearchService(Protocol):
    def index(self, document: SearchDocument) -> None:
        ...

    def search(self, query: SearchQuery) -> list[SearchDocument]:
        ...


class InMemorySearchService:
    def __init__(self) -> None:
        self._rows: list[SearchDocument] = []

    def index(self, document: SearchDocument) -> None:
        if int(document.tenant_id) <= 0:
            raise ValueError("tenant_id is required")
        self._rows.append(document)

    def search(self, query: SearchQuery) -> list[SearchDocument]:
        if int(query.tenant_id) <= 0:
            raise ValueError("tenant_id is required")
        needle = query.text.strip().lower()
        if not needle:
            return []
        result: list[SearchDocument] = []
        for item in self._rows:
            if int(item.tenant_id) != int(query.tenant_id):
                continue
            if query.module and item.module != query.module:
                continue
            if query.entity and item.entity != query.entity:
                continue
            haystack = f"{item.title} {item.content}".lower()
            if needle in haystack:
                result.append(item)
            if len(result) >= max(1, min(int(query.limit), 100)):
                break
        return result
