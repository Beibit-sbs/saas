# Pilot Feature Flag Matrix

## Purpose

This matrix records how pilot-visible capabilities are controlled at rollout time.

Important distinction:

- some capabilities are true runtime feature flags
- others are release-gated or permission-gated only

Both must be documented so operations knows what can be disabled quickly during pilot support.

## Matrix

| Capability | Control type | Key / mechanism | Default | Pilot posture | Fast rollback path |
| --- | --- | --- | --- | --- | --- |
| Local users admin tab | runtime feature flag | `admin.local_users.tab` | enabled | enabled for pilot admin teams | set flag to `false` per tenant or globally |
| Ops Console v1.1 | permission-gated | frontend `ops.read` / `ops.write` + backend admin/internal routes | visible only to authorized users | enabled | remove role visibility; keep backend routes restricted |
| Automation workflow engine | release-gated | backend routes + automation rule activation | enabled in code, inactive until rules exist | enable only reviewed rules | deactivate offending rules |
| Webhook delivery and retry | release-gated | backend service + internal retry endpoints | enabled | enabled with monitored subscriptions only | deactivate subscription per tenant |
| KPI refresh and rector dashboard | release-gated | internal refresh routes + dashboard endpoints | enabled | enabled | stop scheduler refresh or hide dashboard route |
| AI Copilot admin answers | release-gated | admin route + RBAC | enabled | enabled for pilot admins only | remove admin access or disable route at reverse proxy |
| Developer platform public APIs | release-gated | developer app install + scope validation | disabled unless app installed | controlled rollout per tenant app | revoke installation or rotate secret |
| Federation surfaces | permission-gated | `federation.read` / `federation.write` | hidden to most users | restricted to approved admins | remove federation permissions |

## Operational Notes

1. Only one true runtime flag exists today in the shared feature-flag store: `admin.local_users.tab`.
2. All other pilot surfaces are currently controlled through permissions, route exposure, installation state, or operational procedure.
3. During pilot support, the preferred first rollback action is permission removal or per-tenant deactivation before code rollback.

## Gaps To Track

- Ops Console does not yet have a backend runtime feature flag.
- AI Copilot and Developer Platform do not yet have dedicated kill switches beyond RBAC and reverse-proxy controls.
- If pilot scope expands, the next increment should add explicit operational kill switches for AI, automation, and public developer APIs.