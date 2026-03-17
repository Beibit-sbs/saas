# RBAC Matrix Template

Define project-specific roles and permissions using this matrix.

## Roles
- superadmin
- admin
- auditor
- custom roles: ...

## Permission Naming Convention
Use dotted namespaces:
- `admin.dashboard.read`
- `admin.roles.manage`
- `admin.audit.read`
- `module.entity.action`

## Matrix
| Permission | superadmin | admin | auditor | custom_role_1 |
|-----------|------------|-------|---------|---------------|
| admin.dashboard.read | Y | Y | Y | |
| admin.roles.manage | Y | Y | | |
| admin.audit.read | Y | Y | Y | |
| module.sample.read | Y | Y | Y | Y |
| module.sample.write | Y | Y | | |

## Notes
- Keep permissions granular and action-based.
- Avoid role-name checks in business code.
- Enforce permissions at endpoint and service layers.
