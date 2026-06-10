"""Reporting Runtime permission constants."""

from __future__ import annotations

READ = "admin.reporting_runtime.read"
SUMMARY_READ = "admin.reporting_runtime.summary.read"

REPORTING_RUNTIME_PERMISSIONS = frozenset({READ, SUMMARY_READ})

REPORTING_RUNTIME_PERMISSION_DESCRIPTIONS = {
    READ: "Read reporting runtime shell foundation endpoints.",
    SUMMARY_READ: "Read reporting runtime shell summary endpoint.",
}
