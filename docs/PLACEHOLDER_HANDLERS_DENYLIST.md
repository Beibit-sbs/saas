# Placeholder Job Handlers — Production De-Scope

## Summary

Four job handler types are defined as **placeholders** (no-op stubs) and are **explicitly blocked in production mode**:

1. `sync` — Legacy sync task (not yet implemented)
2. `ldap.sync` — LDAP synchronization task (not yet implemented)
3. `ai.generate` — AI generation task (not yet implemented)
4. `report.generate` — Report generation task (not yet implemented)

## Production Safety

These handlers are guarded by a production-mode check in [backend/app/modules/jobs/worker.py](../backend/app/modules/jobs/worker.py):

```python
def _execute_placeholder(job: JobRecord) -> dict[str, Any]:
    if is_production_mode():
        raise RuntimeError(
            f"Job type '{job.job_type}' is a placeholder and not available in production. "
            f"Implement concrete handler or remove from product scope."
        )
    return {"status": "placeholder_noop", "job_type": job.job_type}
```

**Result**: Any attempt to execute these job types in a production environment will fail with a clear error message.

## Current Usage

- **Tests only**: These types are used in unit and integration tests to verify job system mechanics.
- **Frontend**: No UI entry point exists to enqueue these job types (not exposed in job creation forms).
- **Backend API**: The `/api/admin/jobs` endpoint accepts any job_type, but execution will fail in production.

## Product Scope Decision

### Option A: Implement Concrete Handlers
If the feature is required, implement the actual handler logic and attach to the same handler registry.

### Option B: Remove from Product Scope (Current)
Document these as **out of scope** and remove:
- All references from test fixtures (except intentional noop tests).
- UI forms that might allow enqueueing these types.
- Documentation that references these as "coming soon."

### Option C: Hybrid
Implement `report.generate` (most likely useful) while keeping others as de-scoped placeholders.

## Verification Checklist

- [x] Production mode check is in place (`is_production_mode()` guard).
- [x] Unit tests verify placeholder behavior in non-production contexts.
- [x] No UI exposes these job types to end users.
- [x] Error message is clear and actionable.
- [ ] Product scope decision is documented and signed off.
- [ ] All placeholder references cleaned up post-decision.

## Deferred Action

This item remains on the cleanup backlog (item C-006 in [CLEANUP_ENDGAME_TRACKER.md](CLEANUP_ENDGAME_TRACKER.md)) pending:
1. Final product scope decision by stakeholders.
2. Implementation of concrete handlers OR explicit de-scope documentation.
3. Cleanup of test/fixture references post-decision.
