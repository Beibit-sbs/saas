# 03 — Полный аудит ролей, RBAC и ABAC

[← 02 Карта зависимостей](02_MODULE_DEPENDENCY_MAP.md) · [Индекс](README.md) · Далее: [04 База данных →](04_DATABASE.md)

Источники: `app/modules/rbac/service.py`, `security.py`, `abac.py`, `router.py`; `app/modules/*/permissions.py`.

---

## 4.1 Модель RBAC

- **Формат permission:** иерархическая строка `{module}.{resource}.{action}` или `{module}.{action}`.
  Примеры: `students.read`, `grades.write`, `campus_facilities.maintenance.read`, `admin.rector_assignments.create`, `student_lifecycle.evidence.attach`.
- **Действия (actions):** `.read`, `.write`/`.create`/`.update`/`.delete`, `.execute`, `.manage`/`.configure`/`.admin`, `.metadata`, `.evidence`/`.audit`, `.attach`.
- **Уровни ролей:**
  1. Платформенные (tenant_id=1): `superadmin`, `platform_admin`.
  2. Тенантные (tenant_id>1): институциональные и доменные роли.
  3. Scopes сервисных токенов (M2M) — фиксированный набор прав в JWT (`token_type=service`).
- **Резолвинг прав:** `resolve_permissions_for_tenant(roles, tenant_id) → Set[str]`; `get_user_roles_for_tenant(user_id, tenant_id)`; `is_platform_admin(user_id)`.
- **Enforcement:** `permission_dependency(permission)` (FastAPI‑зависимость) в `security.py`:
  1. Разбор JWT (user_id, roles, tenant_id). 2. Override тенанта заголовком — только для superadmin. 3. Блок cross‑tenant для платформенного пользователя (кроме RBAC‑admin путей). 4. Резолв ролей из БД (fallback на JWT‑scopes). 5. Проверка `required ∈ granted`. 6. Логирование отказов в аудит.
- **Хранение:** таблицы `user_roles` (user_id, tenant_id, role), `role_permissions` (role, permission; tenant‑scoped); кэш в Redis.

---

## 4.2 Каноничные роли

| Роль | Тенант | Назначение | Права (сводно) |
|------|--------|------------|----------------|
| `superadmin` | Платформа (1) | Оператор платформы | Все права, cross‑tenant override |
| `platform_admin` | Платформа (1) | Администрирование платформы | `_CANONICAL_PLATFORM_ADMIN_PERMISSIONS` (platform.admin.*, analytics, health, metrics, ops, jobs, audit, rbac, tenants + чтение/запись основных доменов) |
| `auditor` | Инстанс | Комплаенс‑аудит (read‑only) | `_CANONICAL_AUDITOR_PERMISSIONS` (все `*.read` по доменам + audit.read) |
| `admin` | Инстанс | Институциональный админ | Полный набор прав инстанса |
| `student` | Инстанс | Самообслуживание студента | `enrollments.read`, `profiles.read`, `advising.read` (+ ABAC на «своё») |
| `rector` | Инстанс | Ректор/руководство | Высокоуровневая видимость + поручения/эскалации (через `rector_assignment_workflow`) |
| `executive_control_tower` | Инстанс | C‑level исполнительный | `_EXECUTIVE_CONTROL_TOWER_PERMISSIONS` (summary, assignments, documents, sla_risk, strategy, audit, department, metric_registry — read) |

### Доменные административные роли (по `permissions.py`/`service.py`)

`student_lifecycle_admin`, `academic_operations_admin`, `research_science_admin`, `quality_accreditation_admin`, `finance_procurement_asset_admin`, `security_access_compliance_admin`, `student_services_support_admin`, `communications_admin` (подразумевается), плюс институт‑определяемые (`finance_officer`, `security_officer`, `hr_director` и т.п.).

> **Оговорка:** точный полный список ролей формируется из маппинга `_TENANT_ROLE_PERMISSIONS` в `service.py` и наборов в `permissions.py`. Часть ролей — институт‑настраиваемые (создаются в конкретном тенанте), поэтому исчерпывающего «жёсткого» списка в коде нет.

---

## 4.3 ABAC (атрибутный контроль доступа)

Файл: `app/modules/rbac/abac.py`. **Дополняет** RBAC: для чувствительных ресурсов требуются обе проверки.

**Атрибуты:** tenant (все ресурсы scoped), ownership (`resource_owner_id`), department/иерархия (членство в орг‑единице), sensitivity (классификация данных), роль актора.

**Примеры правил уровня ресурса:**
- **Student Profiles:** admin — любой студент; student — только свой профиль; advisor/teacher — только закреплённые (если есть маппинг); иначе fail‑closed + запись в аудит.
- **Enrollments:** admin — любые; student — только свои; инструктор курса — записи по своему курсу.
- **Grades:** только инструктор курса/admin — запись/изменение; студент — чтение своих.
- **Courses:** владелец/admin — управление; остальные — чтение.

**Логирование:** `log_data_access_event(actor_id, tenant_id, resource, resource_id, action, result)`.

**Комбинация:** RBAC отвечает «есть ли право `grades.write`?», ABAC — «это ваш курс или вы admin?». Доступ — только при прохождении обеих.

---

## 4.4 Инвентарь permissions по модулям

19 модулей имеют выделенный `permissions.py`. Крупнейшие наборы:

| Модуль | ~Кол‑во permissions | Примеры |
|--------|---------------------|---------|
| `finance_procurement_asset` | 65+ | `budget.*`, `expense.*`, `procurement.*(approve)`, `asset_inventory.*` |
| `academic_operations` | 58+ | `academic_groups.*`, `cohorts.*`, `gradebook_metadata.*`, bridges |
| `campus_facilities_housing_transport` | 53 | `campus/buildings/occupancy/maintenance/transport.read`, `*_bridge.read` |
| `student_lifecycle` | 50+ | `applicants.*`, `students.*`, `enrollment.*`, `appeals.*`, `evidence.attach` |
| `quality_accreditation` | 48+ | `self_assessment.*`, `accreditation_evidence.create`, `corrective_action.*` |
| `research_science` | 40+ | `projects.*`, `publications.*`, `ethics.*`, `grants.*`, `supervision.*` |
| `security_access_compliance` | 37+ | `access_control.read`, `security_event.read`, `compliance_report.read`, `evidence.attach` |
| `digital_twin` | 5 | `state.read`, `safety.read`, `simulate.run`, `decision.record`, `decision.read` |

Прочие с `permissions.py`: `student_services_support`, `admissions_crm`, `reporting_runtime`, `rector_assignment_workflow`, `communications`, `integration_provider_readiness`, `document_workflow_os`, `document_decree_correspondence`, `innovation_commercialization`, `executive_control_tower`, `hr_staff_governance`.

> В остальных модулях права заданы строковыми константами прямо в `router.py` (`permission_dependency("...")`).

---

## 4.5 Проверки, выполняемые при доступе (сводно)

1. Валидна ли аутентификация (JWT из cookie/Bearer)? → иначе 401.
2. Совпадает ли tenant в токене с запросом (fail‑closed)? cross‑tenant — только superadmin → иначе 403.
3. Есть ли требуемый permission у роли (RBAC)? → иначе 403 + аудит.
4. Проходит ли ABAC (ownership/department/sensitivity) для чувствительного ресурса? → иначе 403 + аудит.
5. Не превышен ли rate limit? → иначе 429.
6. Идемпотентность (для мутаций с ключом) — не повтор ли?

---

## 4.6 Аутентификация (сводно)

- **Методы:** local (PBKDF2‑SHA256), LDAP/AD (`/api/auth/login/ldap`), OIDC (identity phase1), SAML 2.0 (`sso_saml`), 2FA/TOTP.
- **Токен (JWT):** claims `user_id, roles, permissions, auth_source, tenant_id, jti, token_type(user|service), session_id, platform_global, issued_at, expires_at`.
- **Сессии:** PostgreSQL; revoke по session_id/jti; revocation в Redis (+ memory).
- **Cookie:** access (`app_access_token`), refresh, csrf; SameSite конфигурируемый; Secure в продакшене.
- **Демо‑доступ:** `demo-users`/`demo-login` — только шаблон/демо, отключить перед продом.

Полный аудит ролей по каждой странице/модулю — см. [pages/README.md](pages/README.md) и файлы [modules/](modules/).
