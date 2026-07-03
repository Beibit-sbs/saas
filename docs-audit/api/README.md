# Каталог API

[← Индекс аудита](../README.md) · Верхнеуровневый обзор: [../05_API.md](../05_API.md)

151 роутер (143 модульных + 8 платформенных), 685+ permission‑guarded endpoint. Полные группы и префиксы — в [../05_API.md](../05_API.md) §6.2.

## Логические группы API (файлы)

| Группа | Файл | Префиксы |
|--------|------|----------|
| Auth API | [auth-api.md](auth-api.md) | `/api/auth` |
| Brain API | [brain-api.md](brain-api.md) | `/api/admin/brain` |
| Platform API | [platform-api.md](platform-api.md) | `/api/v1/*`, `/api/dev`, `/api/v2/semantic` |
| RBAC / Admin API | [rbac-api.md](rbac-api.md) | `/api/admin/rbac`, `/api/admin/*` |

## Доменные API
Каждый доменный модуль экспонирует свой роутер; endpoint'ы, методы, permissions, request/response перечислены в соответствующем файле [../modules/](../modules/). Пример полного контракта — [admissions](../modules/admissions.md) / [../05_API.md](../05_API.md) §6.3.

## Конвенции
- Формат permission: `{module}.{resource}.{action}`.
- Аутентификация: JWT cookie/Bearer; developer — `X‑App‑Key/Secret`; internal/mcp — Bearer scopes.
- Коды ошибок: 400/401/403/404/409/429 (унифицировано `router_errors.py`).
- **Источник истины по endpoint'ам:** OpenAPI работающего backend (`/docs`, `/openapi.json`).

## Замечание об объёме
Поштучные файлы на каждый из 685+ endpoint'ов не создавались (нецелесообразно и дублирует OpenAPI). API документированы: (1) сводно по группам здесь и в [../05_API.md](../05_API.md); (2) по модулям в [../modules/](../modules/); (3) детально по ключевым системным группам в файлах ниже.
