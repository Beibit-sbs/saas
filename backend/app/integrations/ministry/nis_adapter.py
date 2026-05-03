"""L.5 — Ministry of Education NIS adapter (stub)."""
from __future__ import annotations

import httpx

NIS_BASE_URL = "https://nis.edu.kz/api/v2"
DEFAULT_TIMEOUT = 30


class NisAdapterError(Exception):
    pass


def push_student_data(tenant_id: str, students: list[dict]) -> dict:
    """Push student personal/enrollment data to Ministry NIS. Returns sync result."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not isinstance(students, list):
        raise ValueError("students must be a list")

    payload = {
        "tenantId": tenant_id,
        "students": students,
    }
    try:
        resp = httpx.post(f"{NIS_BASE_URL}/students/sync", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise NisAdapterError(f"NIS push_student_data failed: {exc}") from exc

    return {
        "accepted": data.get("accepted", 0),
        "rejected": data.get("rejected", 0),
        "errors": data.get("errors", []),
        "sync_id": data.get("syncId", ""),
    }


def push_grades(tenant_id: str, grades: list[dict]) -> dict:
    """Push grade records to Ministry NIS."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not isinstance(grades, list):
        raise ValueError("grades must be a list")

    payload = {
        "tenantId": tenant_id,
        "grades": grades,
    }
    try:
        resp = httpx.post(f"{NIS_BASE_URL}/grades/sync", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise NisAdapterError(f"NIS push_grades failed: {exc}") from exc

    return {
        "accepted": data.get("accepted", 0),
        "rejected": data.get("rejected", 0),
        "errors": data.get("errors", []),
        "sync_id": data.get("syncId", ""),
    }


def push_enrollment_stats(tenant_id: str, stats: dict) -> dict:
    """Push enrollment statistics to Ministry NIS (nightly sync)."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not isinstance(stats, dict):
        raise ValueError("stats must be a dict")

    payload = {
        "tenantId": tenant_id,
        "stats": stats,
    }
    try:
        resp = httpx.post(f"{NIS_BASE_URL}/enrollment/stats", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise NisAdapterError(f"NIS push_enrollment_stats failed: {exc}") from exc

    return {
        "status": data.get("status", "ACCEPTED"),
        "report_id": data.get("reportId", ""),
    }
