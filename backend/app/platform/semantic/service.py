from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.modules.observability.metrics import snapshot_latency_metrics
from app.platform.kpi import service as kpi_service
from app.platform.semantic import registry
from app.platform.semantic.schemas import (
    SemanticDimensionSchema,
    SemanticEntitySchema,
    SemanticInsightReadSchema,
    SemanticMetricSchema,
    SemanticQueryMetadataSchema,
    SemanticQueryRequestSchema,
    SemanticQueryResponseSchema,
)


@dataclass
class SemanticScope:
    role_scope: str
    actor_id: str
    required_filters: dict[str, str]
    restricted_dimensions: set[str]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_semantic_entities() -> list[SemanticEntitySchema]:
    rows: list[SemanticEntitySchema] = []
    for code, item in registry.ENTITIES.items():
        rows.append(
            SemanticEntitySchema(
                code=code,
                version=registry.SEMANTIC_VERSION,
                description=str(item["description"]),
                grain=str(item["grain"]),
                allowed_dimensions=list(item["allowed_dimensions"]),
                allowed_metrics=list(item["allowed_metrics"]),
            )
        )
    rows.sort(key=lambda row: row.code)
    return rows


def list_semantic_metrics() -> list[SemanticMetricSchema]:
    rows: list[SemanticMetricSchema] = []
    for code, item in registry.METRICS.items():
        rows.append(
            SemanticMetricSchema(
                code=code,
                version=registry.SEMANTIC_VERSION,
                description=str(item["description"]),
                source=str(item["source"]),
                aggregation=str(item["aggregation"]),
                time_grains=list(item["time_grains"]),
                tenant_scope=str(item["tenant_scope"]),
                entity=str(item["entity"]),
            )
        )
    rows.sort(key=lambda row: row.code)
    return rows


def list_semantic_dimensions() -> list[SemanticDimensionSchema]:
    rows: list[SemanticDimensionSchema] = []
    for code, item in registry.DIMENSIONS.items():
        rows.append(
            SemanticDimensionSchema(
                code=code,
                version=registry.SEMANTIC_VERSION,
                description=str(item["description"]),
                allowed_entities=list(item["allowed_entities"]),
                allowed_metrics=list(item["allowed_metrics"]),
            )
        )
    rows.sort(key=lambda row: row.code)
    return rows


def build_semantic_scope(*, actor_id: str, roles: list[str]) -> SemanticScope:
    normalized_roles = {str(role).strip().lower() for role in roles if str(role).strip()}

    if {"superadmin", "admin", "rector"} & normalized_roles:
        return SemanticScope(
            role_scope="tenant_full",
            actor_id=actor_id,
            required_filters={},
            restricted_dimensions=set(),
        )

    if "dean" in normalized_roles:
        return SemanticScope(
            role_scope="program_or_department",
            actor_id=actor_id,
            required_filters={},
            restricted_dimensions={"tenant"},
        )

    if {"teacher", "instructor"} & normalized_roles:
        return SemanticScope(
            role_scope="instructor_self",
            actor_id=actor_id,
            required_filters={"instructor": actor_id},
            restricted_dimensions={"tenant"},
        )

    raise HTTPException(status_code=403, detail="semantic access denied for current role")


def _validate_request(request: SemanticQueryRequestSchema, scope: SemanticScope) -> dict[str, str]:
    entity = request.entity.strip().lower()
    if entity not in registry.ENTITIES:
        raise HTTPException(status_code=400, detail=f"unknown semantic entity: {entity}")

    if request.time_range not in registry.SUPPORTED_TIME_RANGES:
        raise HTTPException(status_code=400, detail=f"unsupported time_range: {request.time_range}")

    entity_info = registry.ENTITIES[entity]
    allowed_dimensions = set(entity_info["allowed_dimensions"])
    allowed_metrics = set(entity_info["allowed_metrics"])

    for metric in request.metrics:
        metric_code = metric.strip().lower()
        if metric_code not in registry.METRICS:
            raise HTTPException(status_code=400, detail=f"unknown semantic metric: {metric_code}")
        if metric_code not in allowed_metrics:
            raise HTTPException(status_code=400, detail=f"metric {metric_code} is not allowed for entity {entity}")

    normalized_dimensions: list[str] = []
    for dimension in request.dimensions:
        dim = dimension.strip().lower()
        if dim not in registry.DIMENSIONS:
            raise HTTPException(status_code=400, detail=f"unknown semantic dimension: {dim}")
        if dim not in allowed_dimensions:
            raise HTTPException(status_code=400, detail=f"dimension {dim} is not allowed for entity {entity}")
        if dim in scope.restricted_dimensions:
            raise HTTPException(status_code=403, detail=f"dimension {dim} is not allowed for role scope")
        normalized_dimensions.append(dim)

    normalized_filters = {str(key).strip().lower(): str(value) for key, value in request.filters.items()}
    for key in normalized_filters:
        if key not in allowed_dimensions:
            raise HTTPException(status_code=400, detail=f"filter {key} is not allowed for entity {entity}")

    if scope.role_scope == "program_or_department":
        if "program" not in normalized_filters and "department" not in normalized_filters:
            raise HTTPException(status_code=403, detail="dean scope requires program or department filter")

    for key, value in scope.required_filters.items():
        existing = normalized_filters.get(key)
        if existing is not None and existing != value:
            raise HTTPException(status_code=403, detail=f"scope filter mismatch for {key}")
        normalized_filters[key] = value

    return normalized_filters


def _metric_value(metric: str, *, metric_values: dict[str, int], latency_values: dict[str, float]) -> float:
    total_students = float(metric_values.get("total_students", 0))
    total_enrollments = float(metric_values.get("total_enrollments", 0))
    total_grades = float(metric_values.get("total_grades_submitted", 0))
    failed_jobs = float(metric_values.get("total_failed_jobs", 0))
    failed_notifications = float(metric_values.get("total_failed_notifications", 0))

    if metric == "student.success_rate":
        if total_enrollments <= 0:
            return 0.0
        return round(min(total_grades / total_enrollments, 1.0), 4)

    if metric == "student.dropout_risk":
        denominator = max(total_students, 1.0)
        return round(min((failed_jobs + failed_notifications) / denominator, 1.0), 4)

    if metric == "course.pass_rate":
        if total_enrollments <= 0:
            return 0.0
        return round(min(total_grades / total_enrollments, 1.0), 4)

    if metric == "faculty.workload_index":
        denominator = max(total_students, 1.0)
        return round(total_grades / denominator, 4)

    if metric == "ops.latency_p95":
        return float(latency_values.get("p95_latency_ms", 0.0) or 0.0)

    return 0.0


def run_semantic_query(
    *,
    tenant_id: int,
    request: SemanticQueryRequestSchema,
    scope: SemanticScope,
    uow: Any,
) -> SemanticQueryResponseSchema:
    normalized_filters = _validate_request(request, scope)
    metric_rows = kpi_service.get_latest_tenant_metrics(tenant_id=tenant_id, uow=uow)
    metric_values = {str(item["metric_key"]): int(item["metric_value"]) for item in metric_rows}
    latency_values = snapshot_latency_metrics()

    record: dict[str, Any] = {
        "entity": request.entity.strip().lower(),
        "time_range": request.time_range,
    }
    for key, value in normalized_filters.items():
        record[key] = value

    normalized_metrics = [metric.strip().lower() for metric in request.metrics]
    for metric in normalized_metrics:
        record[metric] = _metric_value(metric, metric_values=metric_values, latency_values=latency_values)

    data_as_of = _now_iso()
    lineage_ref = f"semantic:{request.entity.strip().lower()}:{tenant_id}:{int(datetime.now(timezone.utc).timestamp())}"

    metadata = SemanticQueryMetadataSchema(
        entity=request.entity.strip().lower(),
        metrics_returned=normalized_metrics,
        dimensions_applied=[item.strip().lower() for item in request.dimensions],
        filters_applied=normalized_filters,
        tenant_id=int(tenant_id),
        role_scope=scope.role_scope,
        semantic_version=registry.SEMANTIC_VERSION,
        lineage_ref=lineage_ref,
        data_as_of=data_as_of,
    )

    explanation: str | None = None
    if request.explain:
        explanation = (
            f"Semantic query for entity '{metadata.entity}' evaluated from precomputed KPI and ops snapshots "
            f"under role scope '{metadata.role_scope}'."
        )

    return SemanticQueryResponseSchema(
        data=[record],
        metadata=metadata,
        lineage_ref=lineage_ref,
        data_as_of=data_as_of,
        explanation=explanation,
    )


def build_scorecard(*, tenant_id: int, uow: Any, scope: SemanticScope) -> SemanticQueryResponseSchema:
    request = SemanticQueryRequestSchema(
        entity="scorecard",
        metrics=[
            "student.success_rate",
            "student.dropout_risk",
            "course.pass_rate",
            "faculty.workload_index",
            "ops.latency_p95",
        ],
        dimensions=["term"],
        filters={},
        time_range="last_30_days",
        explain=True,
    )
    return run_semantic_query(tenant_id=tenant_id, request=request, scope=scope, uow=uow)


def build_insight(
    *,
    tenant_id: int,
    entity: str,
    metric: str,
    scope: SemanticScope,
    uow: Any,
) -> SemanticInsightReadSchema:
    response = run_semantic_query(
        tenant_id=tenant_id,
        request=SemanticQueryRequestSchema(
            entity=entity,
            metrics=[metric],
            dimensions=[],
            filters={},
            time_range="last_30_days",
            explain=True,
        ),
        scope=scope,
        uow=uow,
    )
    value = float(response.data[0].get(metric, 0.0))
    return SemanticInsightReadSchema(
        entity=entity,
        metric=metric,
        value=value,
        explanation=response.explanation or "Insight explanation unavailable",
        lineage_ref=response.lineage_ref,
        data_as_of=response.data_as_of,
    )
