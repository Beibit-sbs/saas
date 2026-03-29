from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/public", tags=["platform-core-public"])


# ============================================================================
# All public endpoints removed:
# - No tenant metadata endpoints (/tenants/{id})
# - No developer/partner endpoints (/students, /enrollments, etc.)
#   → Moved to /api/dev (router_developer_api.py)
#
# This router is RESERVED for truly public endpoints (if any):
# - Health checks, status pages, public docs
# ============================================================================

