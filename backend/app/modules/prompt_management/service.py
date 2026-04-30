"""Phase XII-XII3: Prompt Management service — module-level in-memory store."""
from __future__ import annotations

import hashlib
from threading import Lock

from app.modules.prompt_management.schemas import (
    ABTestResultSchema,
    ABTestRouteSchema,
    PromptTemplateCreateSchema,
    PromptTemplateReadSchema,
    PromptTemplateUpdateSchema,
)

# Module-level store — NOT cleared by clear_university_state()
_store: dict[str, dict] = {}  # template_id -> record
_store_lock = Lock()


def _gen_id(tenant_id: int, name: str, version: int) -> str:
    return hashlib.sha256(f"{tenant_id}:{name}:v{version}".encode()).hexdigest()[:16]


def _row_to_read(row: dict) -> PromptTemplateReadSchema:
    variables = row.get("variables") or []
    if isinstance(variables, str):
        import json
        try:
            variables = json.loads(variables)
        except Exception:
            variables = []
    return PromptTemplateReadSchema(
        template_id=str(row["template_id"]),
        name=str(row["name"]),
        description=row.get("description"),
        template_text=str(row["template_text"]),
        variables=variables,
        category=str(row.get("category", "general")),
        version=int(row.get("version", 1)),
        is_active=bool(row.get("is_active", True)),
        created_by=str(row.get("created_by", "")),
        created_at=str(row.get("created_at", "")),
    )


def create_template(
    *,
    tenant_id: int,
    actor_id: str,
    payload: PromptTemplateCreateSchema,
) -> PromptTemplateReadSchema:
    from datetime import datetime, timezone
    with _store_lock:
        same_name = [r for r in _store.values() if r.get("tenant_id") == tenant_id and r.get("name") == payload.name]
        version = max((int(r.get("version", 1)) for r in same_name), default=0) + 1
        template_id = _gen_id(tenant_id, payload.name, version)
        record = {
            "template_id": template_id,
            "tenant_id": tenant_id,
            "name": payload.name,
            "description": payload.description,
            "template_text": payload.template_text,
            "variables": list(payload.variables or []),
            "category": payload.category or "general",
            "version": version,
            "is_active": payload.is_active if payload.is_active is not None else True,
            "created_by": actor_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _store[template_id] = record
    return _row_to_read(record)


def list_templates(
    *,
    tenant_id: int,
    category: str | None = None,
    active_only: bool = False,
) -> list[PromptTemplateReadSchema]:
    with _store_lock:
        rows = [r for r in _store.values() if r.get("tenant_id") == tenant_id]
    if category:
        rows = [r for r in rows if str(r.get("category")) == category]
    if active_only:
        rows = [r for r in rows if r.get("is_active") not in (False, "false", "0")]
    return [_row_to_read(r) for r in rows]


def update_template(
    *,
    tenant_id: int,
    template_id: str,
    payload: PromptTemplateUpdateSchema,
) -> PromptTemplateReadSchema | None:
    with _store_lock:
        existing = _store.get(template_id)
        if existing is None or existing.get("tenant_id") != tenant_id:
            return None
        if payload.description is not None:
            existing["description"] = payload.description
        if payload.template_text is not None:
            existing["template_text"] = payload.template_text
        if payload.variables is not None:
            existing["variables"] = list(payload.variables)
        if payload.is_active is not None:
            existing["is_active"] = payload.is_active
        updated = dict(existing)
    return _row_to_read(updated)


def route_ab_test(
    *,
    tenant_id: int,  # noqa: ARG001
    payload: ABTestRouteSchema,
) -> ABTestResultSchema:
    """Deterministic A/B routing by hashing context_key."""
    h = int(hashlib.sha256(payload.context_key.encode()).hexdigest(), 16) % 100
    variant: str = "A" if h < payload.traffic_split_pct else "B"
    selected = payload.template_id_a if variant == "A" else payload.template_id_b
    return ABTestResultSchema(
        selected_template_id=selected,
        variant=variant,  # type: ignore[arg-type]
        traffic_split_pct=payload.traffic_split_pct,
        context_key=payload.context_key,
    )
