# 13 — Каталог функциональности платформы

[← 12 Project Statistics](12_PROJECT_STATISTICS.md) · [Индекс](README.md)

Источник: `README.md`, `frontend/shared/config/navigation.ts`, `frontend/app/*`, `docs-audit/*`.

---

## Назначение документа

Этот файл отвечает на практический вопрос: **какие функционалы уже есть на платформе**.

Документ сгруппирован по функциональным областям, а не по исходному коду. Для каждой области указано:

- что умеет платформа сейчас;
- где это проявляется в UI/API;
- насколько это выглядит зрелым по коду: `mature`, `partial`, `shell`, `admin-heavy`.

Важно:

- это каталог **фактически реализованных или явно проведённых в коде** возможностей;
- наличие route/page/module не всегда означает полную product-ready зрелость;
- по `README.md` админская/control-plane часть зрелее, чем role-specific порталы.

---

## 13.1 Сводка по платформе

Платформа представляет собой **мультитенантную University OS SaaS-систему** с такими крупными слоями:

1. **Platform Core**: аутентификация, RBAC, аудит, языки, tenants, integrations, backup, observability.
2. **Admin / Console**: административная и операционная панель с большим числом доменных модулей.
3. **Academic Core**: студенты, зачисления, оценки, транскрипты, расписание, admissions, degree progress.
4. **AI / Brain / Analytics**: AI Gateway, Copilot, Brain Core, Digital Twin, KPI и аналитические runtime-модули.
5. **University Vertical Modules**: student services, research, quality, HR, finance, facilities, housing, alumni и др.
6. **Role Portals**: отдельные зоны `student`, `faculty`, `registrar`.

---

## 13.2 Platform Core

### Аутентификация и сессии

Статус: `mature`

Функциональность:

- логин по локальным пользователям;
- платформенный superadmin login;
- JWT + HttpOnly cookie auth;
- CSRF-защита для cookie-auth запросов;
- refresh/logout/session probe;
- MFA-поток для аккаунтов, где MFA включён;
- tenant-aware login с выбором организации на странице входа;
- login-directory для публичного выбора tenant;
- demo-accounts для локального/demo режима.

Где видно:

- `frontend/app/login/*`
- `frontend/app/api/auth/*`
- `backend/app/modules/auth/*`

### Мультитенантность и tenant governance

Статус: `mature`

Функциональность:

- tenant-scoped доступ к данным;
- tenant bootstrap и trusted tenant context;
- platform-level tenancy management;
- tenant selection на логине;
- tenant-aware routing и permissions.

### RBAC / permissions / доступ

Статус: `mature`

Функциональность:

- роли: `superadmin`, `admin`, `auditor`, `dean`, `teacher`, `student`, `faculty`, `registrar`;
- permissions-driven guards на frontend и backend;
- управление ролями и локальными пользователями;
- support для platform billing access и console access;
- role-based navigation profiles.

Где видно:

- `frontend/shared/config/permissions.ts`
- `frontend/shared/config/role-catalog.ts`
- `frontend/shared/ui/permission-gate.tsx`
- `backend/app/modules/rbac/*`

### Языки и локализация

Статус: `mature`

Функциональность:

- системные языки `kk`, `ru`, `en`;
- language registry;
- language switcher в UI;
- хранение пользовательского языка в профиле/сессии.

### Аудит и журналирование

Статус: `mature`

Функциональность:

- аудит административных и системных действий;
- фильтрация по actor/action/entity/result/correlation id;
- JSON/CSV export;
- audit trail в ключевых бизнес-модулях.

### Интеграции

Статус: `mature` для каркаса, `partial` по части конкретных провайдеров

Функциональность:

- LDAP / Active Directory integration settings;
- AI provider configuration;
- webhooks / integrations surface;
- service accounts / developer platform surfaces.

### Backup / restore

Статус: `mature`

Функциональность:

- backup profiles;
- retention dry-run/apply;
- restore dry-run/execute;
- настраиваемые backup roots и retention rules.

### Feature flags

Статус: `partial`

Функциональность:

- visibility и toggle из admin UI;
- инфраструктурный каркас фичефлагов;
- по `README.md` модуль есть, но по глубине это скорее scaffold/platform baseline.

### Health / metrics / ops

Статус: `mature`

Функциональность:

- health snapshot;
- metrics / observability surfaces;
- ops console;
- jobs / background processing visibility;
- Prometheus / Grafana / Nginx / Docker deployment stack.

---

## 13.3 Admin Console и Control Plane

Статус: `mature`, это самая зрелая часть UI

Главные консольные функции:

- dashboard / overview;
- platform control plane;
- tenants;
- billing plans и usage quotas;
- feature flags;
- jobs;
- interventions;
- notifications;
- health & metrics;
- ops;
- integrations / webhooks;
- automation rules и executions;
- service accounts;
- AI copilot;
- Brain Core policy/intelligence surfaces;
- AI cost / routing;
- federation;
- developer apps.

Это фактически **операционная командная панель платформы**, а не только учебный портал.

---

## 13.4 Academic Core

Статус: `mature`/`admin-heavy`

### Students

- реестр студентов;
- просмотр карточек студентов;
- связь со связанными academic-модулями.

### Enrollments

- список зачислений;
- фильтрация по статусу;
- создание enrollment;
- drop enrollment;
- drawer/detail view.

### Grades

- просмотр grade-related данных;
- grading flows;
- integration с enrollments и transcript surfaces.

### Transcripts

- transcript pages;
- transcript/read-only academic records surfaces.

### Degree Progress

- degree progress overview;
- student academic progression monitoring.

### Scheduling

- академическое расписание;
- section-aware scheduling;
- связи с enrollments и operational modules.

### Events Management

- отдельный модуль управления событиями/расписанием.

### Admissions

- admissions module;
- admission decisions / document-oriented permission model.

### Thesis / Research Ethics / Advising

- thesis surface;
- research ethics surface;
- advising module.

### Academic Integrity / Accreditation Compliance / Exam surfaces

- academic integrity;
- accreditation compliance;
- exam governance;
- exam proctoring.

---

## 13.5 Student Lifecycle и Support

Статус: `partial` to `mature-by-slice`

Функциональность:

- student success runtime;
- interventions и case management;
- student services;
- student life;
- career services;
- financial aid;
- housing;
- alumni lifecycle;
- profile/preferences flows.

По коду эти возможности присутствуют как отдельные модули, панели и runtime-срезы, но зрелость зависит от конкретной вертикали.

---

## 13.6 Research, Quality, Governance и Reporting

Статус: `partial` to `advanced runtime`

### Research / Science

- research science runtime;
- research brain;
- researchers / scientometrics / research risk;
- innovation / commercialization;
- research ethics.

### Quality / Accreditation

- quality accreditation module;
- evidence / registry / self-assessment / corrective actions / readiness / dashboard.

### Executive Governance

- executive governance runtime;
- control tower;
- decision registry;
- risk heatmap;
- KPI / strategic initiatives.

### Reporting / Ministry / Compliance

- reporting runtime;
- accreditation, compliance, ministry, ranking, regulatory, dashboard, registry.

---

## 13.7 Finance, HR, Facilities и Operations

Статус: `partial` to `broad platform coverage`

Функциональность:

- HR & Payroll;
- delinquency collections;
- expense controls;
- facilities & work orders;
- asset inventory;
- platform and finance operations health surfaces;
- procurement / contracts / supply-related risk slices через Brain и runtime-модули.

Это показывает, что платформа уже вышла за пределы чисто академической системы и охватывает операционный контур университета.

---

## 13.8 AI / Copilot / Brain / Digital Twin

Статус: `advanced`, но не везде product-complete

### AI Gateway

- единый `POST /api/ai/chat`;
- реестр моделей;
- адаптеры провайдеров OpenAI / Gemini / Anthropic / custom;
- usage logging;
- audit hooks.

### Brain Core

- signal intake;
- context build;
- classify;
- reason;
- policy guard;
- action planning;
- dispatch;
- outcome listener;
- learning/tuning.

### Domain Brain verticals

- Student Success;
- Academic Operations;
- Executive Governance;
- Reporting;
- Research Science;
- Quality Accreditation.

### Digital Twin

- what-if / predictive operations;
- state and safety-boundary views;
- reuse of signals from multiple domains;
- fail-closed rule set for autonomous actions.

### AI-adjacent modules

- faculty copilot;
- knowledge retrieval;
- prompt management;
- model evaluation;
- AI cost governance;
- AI routing control;
- AI guardrails-related surfaces.

---

## 13.9 Role Portals

Статус: `initial`, `shell`, `partial`

### Student Portal

Есть:

- отдельная зона `/student`;
- portal shell;
- быстрые входы в enrollment/grades/transcript/profile сценарии.

Ограничение:

- по `README.md` это ещё не полный end-to-end production-grade student journey.

### Faculty Portal

Есть:

- отдельная зона `/faculty`;
- portal shell;
- акценты на roster, grades, schedule.

### Registrar Portal

Есть:

- отдельная зона `/registrar`;
- собственная навигация registrar;
- registrar-safe разделы: admissions, governance, audit, controls.

---

## 13.10 Communications и Documents

Статус: `partial` to `mature-by-module`

Функциональность:

- communications overview;
- notifications / announcement / templates / preferences / audit / emergency / providers surfaces по permission catalog;
- documents module;
- document workflow OS slices.

---

## 13.11 Automation, Workflows и Background Jobs

Статус: `mature` на уровне платформенного каркаса

Функциональность:

- workflow engine / workflow permissions;
- automation rules;
- execution history;
- background jobs;
- scheduler / worker infrastructure;
- outbox-like integration flows и event-driven orchestration.

Поддержка есть как в platform console, так и в доменных модулях.

---

## 13.12 Что уже выглядит наиболее зрелым

Наиболее зрелые функциональные зоны по коду и по `README.md`:

- platform core auth / RBAC / audit / i18n;
- admin console / control plane;
- backups / integrations / local users / roles;
- health / metrics / jobs / ops;
- academic admin surfaces: students / enrollments / grades / transcripts / scheduling;
- AI Gateway и platform-level AI configuration.

---

## 13.13 Что выглядит как partial / shell / staged rollout

Зоны, где функциональность уже есть, но зрелость, скорее всего, не полная:

- student portal как полный self-service продукт;
- faculty portal как законченный instructor UX;
- registrar portal как полный рабочий кабинет;
- часть advanced verticals: quality, research, governance, communications, facilities, HR, finance;
- feature flags и часть observability depth;
- некоторые AI/Brain learning/evaluation integration details.

---

## 13.14 Краткий итог

Если описывать платформу коротко, то сейчас она уже включает:

- **SaaS platform foundation** для мультитенантной системы;
- **административную control-plane платформу**;
- **академическое ядро университета**;
- **AI/Brain/analytics слой**;
- **широкий набор вертикальных модулей** для research, quality, student services, finance, facilities, HR и governance;
- **начальные role-based порталы** для student / faculty / registrar.

То есть это уже не один модуль и не просто шаблон админки, а **большая многофункциональная университетская операционная платформа** с выраженным platform-core и AI-first слоями.