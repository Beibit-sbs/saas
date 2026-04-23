"""Ministry KPI Contract v1.

Cross-tenant reporting layer for Ministry-level access.
Guarantees:
  - Only whitelisted aggregate/trend metrics are exposed (no student-level raw, no PII).
  - Values below the suppression threshold are replaced with a suppressed sentinel
    to prevent re-identification of small cohorts.
  - Every read call is recorded in the caller-supplied audit log.
  - Access requires the ``ministry.kpi.read`` RBAC role (enforced at router layer).
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Contract constants
# ---------------------------------------------------------------------------

MINISTRY_KPI_CONTRACT_VERSION: str = "v1"

# RBAC role required for any ministry KPI read (enforced at router layer).
MINISTRY_KPI_REQUIRED_ROLE: str = "ministry.kpi.read"

# Audit action name emitted on every ministry KPI read.
MINISTRY_KPI_AUDIT_ACTION: str = "ministry.kpi.read"

# Minimum cohort count below which a metric value must be suppressed.
# Prevents statistical re-identification of small student populations.
MINISTRY_KPI_SUPPRESSION_THRESHOLD: int = 5

# Value returned in place of any suppressed metric.
MINISTRY_KPI_SUPPRESSED_SENTINEL: str = "suppressed"

# Aggregate-only metric keys that may be exposed to the Ministry layer.
# Criteria: pure count/aggregate, no student identifiers, no PII.
MINISTRY_KPI_WHITELIST: frozenset[str] = frozenset(
    {
        "total_students",
        "total_enrollments",
        "total_grades_submitted",
    }
)


# ---------------------------------------------------------------------------
# Contract application
# ---------------------------------------------------------------------------


def apply_ministry_kpi_contract(
    kpis: dict[str, int],
    tenant_id: int,
    audit_log: list[dict[str, Any]],
) -> dict[str, int | str]:
    """Filter and suppress KPI data according to Ministry KPI Contract v1.

    Steps applied in order:
    1. Append an audit entry to *audit_log* (always, even for empty input).
    2. Discard any metric key not present in ``MINISTRY_KPI_WHITELIST``.
    3. Replace any value strictly below ``MINISTRY_KPI_SUPPRESSION_THRESHOLD``
       with ``MINISTRY_KPI_SUPPRESSED_SENTINEL``.

    Args:
        kpis: Raw metric key → integer value mapping for a single tenant.
        tenant_id: Identifier of the tenant whose data is being accessed.
        audit_log: Mutable list; an audit dict is appended on each call.

    Returns:
        Filtered dict mapping whitelisted metric key → integer value or
        ``MINISTRY_KPI_SUPPRESSED_SENTINEL``.
    """
    audit_log.append(
        {
            "action": MINISTRY_KPI_AUDIT_ACTION,
            "tenant_id": tenant_id,
            "contract_version": MINISTRY_KPI_CONTRACT_VERSION,
            "keys_requested": sorted(kpis.keys()),
        }
    )

    result: dict[str, int | str] = {}
    for key, value in kpis.items():
        if key not in MINISTRY_KPI_WHITELIST:
            continue
        if value < MINISTRY_KPI_SUPPRESSION_THRESHOLD:
            result[key] = MINISTRY_KPI_SUPPRESSED_SENTINEL
        else:
            result[key] = value
    return result
