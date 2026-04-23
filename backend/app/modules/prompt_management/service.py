"""Phase XII-XII3: Prompt Management service."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.modules.prompt_management.schemas import (
    ABTestResultSchema,
    ABTestRouteSchema,
    PromptTemplateCreateSchema,
    PromptTemplateReadSchema,
    PromptTemplateUpdateSchema,
)

_TEMPLATES: dict[int, list[dict[str, Any]]] = {}  # tenant_id → templates


def _tenant_store(tenant_id: int) -> list[dict[str, Any]]:
    return _TEMPLATES.setdefault(tenant_id, [])


def _gen_id(tenant_id: int, name: str) -> str:
    return hashlib.sha256(f"{tenant_id}:{name}".encode()).hexdigest()[:16]


def create_template(
    *,
    tenant_id: int,
    actor_id: str,
    payload: PromptTemplateCreateSchema,
) -> PromptTemplateReadSchema:
    store = _tenant_store(tenant_id)
    # Find existing versions
    existing = [t for t in store if t["name"] == payload.name]
    version = (max(t["version"] for t in existing) + 1) if existing else 1
    template_id = _gen_id(tenant_id, f"{payload.name}:v{version}")

    record: dict[str, Any] = {
        "template_id": template_id,
        "tenant_id": tenant_id,
        "name": payload.name,
        "description": payload.description,
        "template_text": payload.template_text,
        "variables": payload.variables,
        "category": payload.category,
        "version": version,
        "is_active": payload.is_active,
        "created_by": actor_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store.append(record)
    return PromptTemplateReadSchema(**record)


def list_templates(
    *,
    tenant_id: int,
    category: str | None = None,
    active_only: bool = False,
) -> list[PromptTemplateReadSchema]:
    store = _tenant_store(tenant_id)
    result = store
    if category:
        result = [t for t in result if t["category"] == category]
    if active_only:
        result = [t for t in result if t["is_active"]]
    return [PromptTemplateReadSchema(**t) for t in result]


def update_template(
    *,
    tenant_id: int,
    template_id: str,
    payload: PromptTemplateUpdateSchema,
) -> PromptTemplateReadSchema | None:
    store = _tenant_store(tenant_id)
    for record in store:
        if record["template_id"] == template_id:
            if payload.description is not None:
                record["description"] = payload.description
            if payload.template_text is not None:
                record["template_text"] = payload.template_text
            if payload.variables is not None:
                record["variables"] = payload.variables
            if payload.is_active is not None:
                record["is_active"] = payload.is_active
            return PromptTemplateReadSchema(**record)
    return None


def route_ab_test(
    *,
    tenant_id: int,
    payload: ABTestRouteSchema,
) -> ABTestResultSchema:
    """Deterministic A/B routing by hashing context_key."""
    store = _tenant_store(tenant_id)
    ids = {t["template_id"] for t in store}
    # Validate both exist (lenient: allow if not in store, still route)
    h = int(hashlib.md5(payload.context_key.encode()).hexdigest(), 16) % 100  # noqa: S324
    variant: str = "A" if h < payload.traffic_split_pct else "B"
    selected = payload.template_id_a if variant == "A" else payload.template_id_b  # type: ignore[assignment]
    return ABTestResultSchema(
        selected_template_id=selected,
        variant=variant,  # type: ignore[arg-type]
        traffic_split_pct=payload.traffic_split_pct,
        context_key=payload.context_key,
    )
