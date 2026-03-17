# Feature Flags Checklist

## Scope
Use feature flags for risky rollouts and partial features.

## Design
- Flag key naming convention defined (`domain.feature.action`).
- Owner assigned for every flag.
- Scope defined (`global`, `tenant`, `role`, `user`).
- Default state documented.

## Safety
- Every risky change has a rollback flag.
- Flag evaluation happens in backend for access-critical behavior.
- Frontend flags are advisory and must not replace backend authorization.

## Operations
- Expiry date or cleanup trigger defined.
- Stale flag cleanup task scheduled.
- Audit events recorded for flag changes.

## Testing
- Tests cover both enabled and disabled states.
- CI checks include at least one non-default flag path.
