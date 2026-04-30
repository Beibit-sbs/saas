"""
Teaching Quality Analytics Router
Provides dedicated endpoints at /api/admin/teaching-quality matching the frontend hooks contract.
Delegates to the faculty service layer for persistence.
"""
from __future__ import annotations

import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
import app.modules.teaching_quality.service as _svc

router = APIRouter(prefix="/api/admin/teaching-quality", tags=["teaching-quality"])


def _safe_float(v: object, default: float = 0.0) -> float:
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# GET /faculty/{faculty_id}/kpi
# ---------------------------------------------------------------------------


@router.get("/faculty/{faculty_id}/kpi")
def get_faculty_quality_kpi(
    faculty_id: str,
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    records = _svc.list_teaching_quality(int(tenant["id"]), faculty_id=faculty_id)
    if term_id:
        records = [r for r in records if int(r.get("term_id") or 0) == term_id]

    if not records:
        # Return a minimal default KPI so the UI does not break
        return {
            "faculty_id": faculty_id,
            "faculty_name": "",
            "department": "",
            "term_id": str(term_id),
            "student_satisfaction_score": 0.0,
            "course_completion_rate_pct": 0.0,
            "student_learning_gain_pct": 0.0,
            "peer_review_score": 0.0,
            "instructional_innovation_score": 0.0,
            "overall_quality_score": 0.0,
            "trend_direction": "stable",
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    # Aggregate scores across all records for the term
    avg_quality = sum(_safe_float(r.get("quality_score")) for r in records) / len(records)
    avg_kpi = sum(_safe_float(r.get("kpi_score")) for r in records) / len(records)
    overall = round((avg_quality / 100.0 * 5.0 + avg_kpi / 100.0 * 5.0) / 2, 2)

    return {
        "faculty_id": faculty_id,
        "faculty_name": str(records[0].get("faculty_id") or faculty_id),
        "department": str(records[0].get("department") or ""),
        "term_id": str(term_id),
        "student_satisfaction_score": round(avg_quality / 100.0 * 5.0, 2),
        "course_completion_rate_pct": round(avg_quality, 2),
        "student_learning_gain_pct": round(avg_kpi, 2),
        "peer_review_score": round(avg_kpi / 100.0 * 5.0, 2),
        "instructional_innovation_score": round(overall, 2),
        "overall_quality_score": overall,
        "trend_direction": "stable",
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /dashboard/{department}
# ---------------------------------------------------------------------------


@router.get("/dashboard/{department}")
def get_department_quality_dashboard(
    department: str,
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    all_records = _svc.list_teaching_quality(int(tenant["id"]))
    if term_id:
        all_records = [r for r in all_records if int(r.get("term_id") or 0) == term_id]

    TARGET_SCORE = 70.0
    scores = [_safe_float(r.get("quality_score")) for r in all_records]
    avg = round(sum(scores) / len(scores), 2) if scores else 0.0
    above = sum(1 for s in scores if s >= TARGET_SCORE)
    below = len(scores) - above

    return {
        "department": department,
        "term_id": str(term_id),
        "total_faculty": len({str(r.get("faculty_id")) for r in all_records}),
        "average_quality_score": avg,
        "above_target_count": above,
        "below_target_count": below,
        "improvement_opportunities": [
            str(r.get("improvement_plan"))
            for r in all_records
            if r.get("improvement_plan")
        ][:5],
        "last_aggregated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /benchmarks
# ---------------------------------------------------------------------------


@router.get("/benchmarks")
def get_quality_benchmarks(
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list:
    all_records = _svc.list_teaching_quality(int(tenant["id"]))
    if term_id:
        all_records = [r for r in all_records if int(r.get("term_id") or 0) == term_id]

    def _benchmark(name: str, values: list[float]) -> dict:
        if not values:
            return {
                "metric_name": name,
                "institutional_average": 0.0,
                "departmental_average": 0.0,
                "top_quartile": 0.0,
                "bottom_quartile": 0.0,
                "target_value": 70.0,
            }
        s = sorted(values)
        n = len(s)
        return {
            "metric_name": name,
            "institutional_average": round(sum(s) / n, 2),
            "departmental_average": round(sum(s) / n, 2),
            "top_quartile": round(s[int(n * 0.75)], 2),
            "bottom_quartile": round(s[int(n * 0.25)], 2),
            "target_value": 70.0,
        }

    quality_scores = [_safe_float(r.get("quality_score")) for r in all_records]
    kpi_scores = [_safe_float(r.get("kpi_score")) for r in all_records]
    return [
        _benchmark("quality_score", quality_scores),
        _benchmark("kpi_score", kpi_scores),
    ]


# ---------------------------------------------------------------------------
# GET /report
# ---------------------------------------------------------------------------


@router.get("/report")
def get_quality_report(
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    all_records = _svc.list_teaching_quality(int(tenant["id"]))
    if term_id:
        all_records = [r for r in all_records if int(r.get("term_id") or 0) == term_id]

    scores = [_safe_float(r.get("quality_score")) for r in all_records]
    avg = round(sum(scores) / len(scores), 2) if scores else 0.0

    quality_scores = [_safe_float(r.get("quality_score")) for r in all_records]
    kpi_scores = [_safe_float(r.get("kpi_score")) for r in all_records]

    def _benchmark(name: str, values: list[float]) -> dict:
        if not values:
            return {"metric_name": name, "institutional_average": 0.0, "departmental_average": 0.0,
                    "top_quartile": 0.0, "bottom_quartile": 0.0, "target_value": 70.0}
        s = sorted(values)
        n = len(s)
        return {"metric_name": name, "institutional_average": round(sum(s) / n, 2),
                "departmental_average": round(sum(s) / n, 2),
                "top_quartile": round(s[int(n * 0.75)], 2),
                "bottom_quartile": round(s[int(n * 0.25)], 2), "target_value": 70.0}

    return {
        "term_id": str(term_id),
        "report_generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_faculty_evaluated": len({str(r.get("faculty_id")) for r in all_records}),
        "average_quality_score": avg,
        "benchmarks": [_benchmark("quality_score", quality_scores), _benchmark("kpi_score", kpi_scores)],
        "departments": [],
        "trending_metrics": [
            {"metric_name": "quality_score", "trend": "stable", "change_pct": 0.0},
            {"metric_name": "kpi_score", "trend": "stable", "change_pct": 0.0},
        ],
    }


# ---------------------------------------------------------------------------
# GET /faculty/{faculty_id}/improvements
# ---------------------------------------------------------------------------


@router.get("/faculty/{faculty_id}/improvements")
def get_faculty_improvements(
    faculty_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> list:
    records = _svc.list_teaching_quality(int(tenant["id"]), faculty_id=faculty_id)
    return [
        {
            "faculty_id": faculty_id,
            "record_id": r.get("id"),
            "term_id": r.get("term_id"),
            "improvement_plan": r.get("improvement_plan"),
            "quality_score": r.get("quality_score"),
            "kpi_score": r.get("kpi_score"),
        }
        for r in records
        if r.get("improvement_plan")
    ]


# ---------------------------------------------------------------------------
# POST /faculty/{faculty_id}/metric
# ---------------------------------------------------------------------------


@router.post("/faculty/{faculty_id}/metric")
def record_quality_metric(
    faculty_id: str,
    payload: dict,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    metric_type = str(payload.get("metric_type") or "")
    value = _safe_float(payload.get("value"))
    term_id = int(payload.get("term_id") or 0)

    # Map metric types to quality/kpi score fields
    quality_score = 100.0
    kpi_score = 100.0
    if metric_type in ("satisfaction", "completion", "learning_gain"):
        quality_score = round(value, 2)
    elif metric_type in ("peer_review", "innovation"):
        kpi_score = round(value, 2)
    else:
        quality_score = round(value, 2)
        kpi_score = round(value, 2)

    record_payload = {
        "faculty_id": faculty_id,
        "course_id": str(payload.get("course_id") or f"metric-{metric_type}"),
        "term_id": term_id,
        "quality_score": quality_score,
        "kpi_score": kpi_score,
        "improvement_plan": str(payload.get("measurement_period") or ""),
        "notes": f"metric_type={metric_type} value={value}",
    }
    try:
        record = _svc.create_quality_metric(record_payload, int(tenant["id"]))
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "faculty_id": faculty_id,
        "faculty_name": faculty_id,
        "department": "",
        "term_id": str(term_id),
        "student_satisfaction_score": quality_score / 100.0 * 5.0,
        "course_completion_rate_pct": quality_score,
        "student_learning_gain_pct": kpi_score,
        "peer_review_score": kpi_score / 100.0 * 5.0,
        "instructional_innovation_score": (quality_score + kpi_score) / 200.0 * 5.0,
        "overall_quality_score": round((quality_score + kpi_score) / 200.0 * 5.0, 2),
        "trend_direction": "stable",
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "_record_id": record.get("id"),
    }
