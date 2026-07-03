# API‑группа: RBAC / Admin (`/api/admin/rbac`, `/api/admin/*`)

[← Каталог API](README.md) · Роли/RBAC: [../03_ROLES_AND_RBAC.md](../03_ROLES_AND_RBAC.md)

## RBAC endpoints (`rbac/router.py`, `/api/admin/rbac`)

| Метод | Путь (сводно) | Описание | Permissions |
|-------|---------------|----------|-------------|
| GET | `/api/admin/rbac/roles` | Список ролей | `rbac.read` |
| POST | `/api/admin/rbac/roles` | Создать роль | `rbac.write` |
| GET | `/api/admin/rbac/permissions` | Список permissions | `rbac.read` |
| POST | `/api/admin/rbac/assignments` | Назначить роль пользователю | `rbac.write` |
| DELETE | `/api/admin/rbac/assignments/...` | Отозвать роль | `rbac.write` |

## Admin‑агрегатор (`/api/admin/*`)
Каждый доменный `/api/admin/<module>` роутер защищён `permission_dependency`. Middleware `main.py` извлекает модуль из пути (`_extract_admin_module_from_path`) с историческими алиасами: `org→faculty`, `org-units→org_structure`, `research-grants→research`, `accreditation-compliance→accreditation`, `ops→operations`, `university/records→academic_records`.

## Механика проверки
1. JWT claims → 2. tenant match (fail‑closed, cross‑tenant только superadmin) → 3. `resolve_permissions_for_tenant(roles, tenant)` → 4. `required ∈ granted` → 5. ABAC (для чувствительных) → 6. аудит отказов.

## Связанные
`service_accounts` (`/api/admin/service-accounts`), `identity`, `ldap`, `audit`. Детали — [../03_ROLES_AND_RBAC.md](../03_ROLES_AND_RBAC.md).
