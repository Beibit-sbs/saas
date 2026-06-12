"""Student Success Runtime dependency helpers."""

from __future__ import annotations

from fastapi import Depends

from app.modules.student_lifecycle.dependencies import require_student_lifecycle_tenant


def require_student_success_tenant(tenant_id: int = Depends(require_student_lifecycle_tenant)) -> int:
    return tenant_id
