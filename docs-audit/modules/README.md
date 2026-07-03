# Каталог модулей (Modules Catalog)

[← Индекс аудита](../README.md)

Полный каталог всех backend‑модулей (`backend/app/modules/`, ~241) и frontend‑модулей (`frontend/modules/`, ~81), сгруппированных по доменам. Для ключевых модулей есть отдельные файлы (ссылки в таблицах). Остальные документированы строкой назначения здесь — **ни один модуль не пропущен**.

> Стандартная структура backend‑модуля: `router.py` (API) · `service.py` (логика) · `schemas.py` (DTO) · `models.py` (ORM) · `repository.py` (DAL) · `business_rules.py` · `dependencies.py` · `permissions.py`. Фактически многие модули не содержат весь набор (см. [../12_PROJECT_STATISTICS.md](../12_PROJECT_STATISTICS.md)).

## Отдельные файлы по ключевым модулям

| Модуль | Файл |
|--------|------|
| Admissions / Admissions CRM | [admissions.md](admissions.md) |
| Academic Operations | [academic-operations.md](academic-operations.md) |
| Student Lifecycle | [student-lifecycle.md](student-lifecycle.md) |
| Student Success | [student-success.md](student-success.md) |
| Quality & Accreditation | [quality-accreditation.md](quality-accreditation.md) |
| Research & Science / Innovation | [research-science.md](research-science.md) |
| Executive Governance / Control Tower | [executive-governance.md](executive-governance.md) |
| Finance / Procurement / Asset | [finance-procurement-asset.md](finance-procurement-asset.md) |
| HR / Staff Governance | [hr-staff-governance.md](hr-staff-governance.md) |
| Document / Decree / Correspondence | [documents.md](documents.md) |
| Security / Access / Compliance | [security-access-compliance.md](security-access-compliance.md) |
| Campus / Facilities / Housing / Transport | [campus-facilities.md](campus-facilities.md) |
| Communications | [communications.md](communications.md) |
| Brain Core | [../brains/brain-core.md](../brains/brain-core.md) |
| Digital Twin | [../brains/digital-twin.md](../brains/digital-twin.md) |
| AI Gateway & AI‑слой | [ai.md](ai.md) |
| Platform Core (инфраструктура) | [platform-core.md](platform-core.md) |
| Auth / Identity / RBAC | [auth-identity.md](auth-identity.md) |
| Scheduling / Timetable Workflow | [scheduling-timetable.md](scheduling-timetable.md) |
| Reporting Runtime (Ministry) | [../brains/reporting-ministry.md](../brains/reporting-ministry.md) |

---

## 1. Академическое ядро и операции

| Модуль | Назначение |
|--------|-----------|
| `university_core` | **Центральный реестр сущностей** (211 EntityConfig), tenant‑entity API, readiness. |
| `academic_operations` | Академические операции: группы, когорты, gradebook, расписание (агрегатор). См. [academic-operations.md](academic-operations.md). |
| `academic_operations_runtime` | Runtime‑shell + под‑runtime академ‑операций (registry, curriculum, timetable, attendance, assessment, teaching_load, internship, signals, dashboard). |
| `academic_records` | Академические записи студентов. |
| `courses` | Каталог курсов, prerequisites. |
| `course_catalog_management` | Управление каталогом курсов (расширение). |
| `course_learning_outcomes` | Результаты обучения по курсу. |
| `program_learning_outcomes` | Результаты обучения по программе. |
| `programs` | Образовательные программы. |
| `curriculum_mapping` | Карта учебного плана. |
| `curriculum_gap_signal_registry` | Сигнальный реестр пробелов учебного плана (L2, UCE‑132). |
| `academic_quality_signal_registry` | Сигнальный реестр академ‑качества (L2, UCE‑051). |
| `competency_framework` | Фреймворк компетенций. |
| `elective_course_selection` | Выбор элективных курсов. |
| `prerequisite_management` | Управление пререквизитами. |
| `enrollments` | Зачисление, термы, статусы (enum EnrollmentStatus/Type). |
| `grades` | Оценивание. |
| `transcripts` | Транскрипты. |
| `degree_progress` | Прогресс по программе. |
| `degree_audit` | Аудит степени. |
| `transfer_credit_management` | Перезачёт кредитов. |
| `scheduling` | Расписание. См. [scheduling-timetable.md](scheduling-timetable.md). |
| `attendance` | Посещаемость. |
| `syllabus_governance` | Управление силлабусами (governance). |
| `syllabus_management` | Ведение силлабусов. |
| `teaching_quality` | Качество преподавания. |
| `teaching_load_contracts` | Контракты учебной нагрузки. |
| `workload_management` | Балансировка нагрузки. |
| `exam_governance` | Управление экзаменами. |
| `exam_proctoring` | Прокторинг. |
| `exam_integrity_analytics` | Аналитика целостности экзаменов. |
| `academic_integrity` | Академическая честность (кейсы). |
| `academic_integrity_case_management` | Управление кейсами честности. |
| `academic_appeals_workflow` | Апелляции (академ). |
| `student_appeals_workflow` | Апелляции студентов. |
| `thesis` | Дипломные/диссертации. |
| `thesis_dissertation_management` | Управление тезисами/диссертациями. |
| `internship` | Стажировки. |
| `internship_marketplace` | Маркетплейс стажировок. |
| `joint_program_management` | Совместные программы. |
| `lms_content` | Контент СДО. |
| `lms_assessment_center` | Центр оценивания СДО. |
| `advising` | Академическое консультирование. |

## 2. Приём (Admissions)

| Модуль | Назначение |
|--------|-----------|
| `admissions` | Приём: абитуриенты, заявления, этапы, документы, решения. См. [admissions.md](admissions.md). |
| `admissions_crm` | CRM приёма (воронка, лиды). **Не закоммичен (P1).** |
| `ai_admissions_scoring` | AI‑скоринг заявлений. |

## 3. Жизненный цикл и успех студента

| Модуль | Назначение |
|--------|-----------|
| `student_lifecycle` | Жизненный цикл: абитуриент→выпускник. См. [student-lifecycle.md](student-lifecycle.md). |
| `students` | Профили студентов. |
| `student_portal` | Портал студента (backend). |
| `student_success_runtime` | Runtime‑brain успеха студента (8 под‑роутеров). См. [student-success.md](student-success.md). |
| `student_success_analytics` | Аналитика успеха студента (дубль‑семейство). |
| `student_risk_signal_registry` | Сигнальный реестр рисков студента (L2, UCE‑049). |
| `interventions` | Интервенции: кейсы, playbooks, risk, effectiveness. |
| `counseling` | Консультирование. |
| `counseling_case_management` | Управление кейсами консультирования. |
| `disability_support_services` | Поддержка студентов с инвалидностью. |
| `health_services` | Медицинские сервисы. |
| `student_feedback` | Обратная связь студентов. |
| `student_ai_tutor` | AI‑репетитор. |
| `student_id_card` | Студенческие ID‑карты. |
| `student_life` | Студенческая жизнь. |
| `student_services` | Студенческие сервисы (дубль). |
| `student_services_support` | Поддержка студенческих сервисов (welfare). |
| `student_financial_hardship` | Финансовые трудности студента (hardship). |
| `career_services` | Карьерные сервисы. |
| `scholarship` | Стипендии. |
| `scholarship_committee_workflow` | Комитет по стипендиям. |
| `financial_aid` | Финансовая помощь. |
| `alumni` | Выпускники. |
| `alumni_relations_ops` | Операции по связям с выпускниками. |
| `alumni_donation_portal` | Портал пожертвований выпускников. |
| `donations_fundraising` | Фандрайзинг. |
| `parent_portal` | Портал родителей. |
| `parent_engagement` | Вовлечение родителей. |

## 4. Финансы / Закупки / Активы

| Модуль | Назначение |
|--------|-----------|
| `finance_procurement_asset` | Финансы+закупки+активы (агрегатор). См. [finance-procurement-asset.md](finance-procurement-asset.md). |
| `budget_planning` | Бюджетное планирование. |
| `expense_controls` | Контроль расходов. |
| `finance_anomaly_signal_registry` | Сигнальный реестр финансовых аномалий (L2, UCE‑050). |
| `procurement` | Закупки. |
| `procurement_approval_workflow` | Workflow согласования закупок. |
| `procurement_plan_approval_workflow` | Согласование планов закупок. |
| `procurement_risk_signal_registry` | Сигнальный реестр рисков закупок (L2, UCE‑129). |
| `asset_inventory` | Инвентаризация активов. |
| `delinquency_collections` | Взыскание задолженностей. |
| `online_payments` | Онлайн‑платежи. |
| `payment_reconciliation` | Сверка платежей. |
| `invoices` | Счета. |
| `billing` | Биллинг тенантов (SaaS). |
| `plans` | Тарифные планы. |
| `subscriptions` | Подписки. |
| `quotas` | Квоты. |
| `usage` | Учёт использования. |
| `currency_localization` | Мультивалютность/локализация. |

## 5. HR / Персонал

| Модуль | Назначение |
|--------|-----------|
| `hr_staff_governance` | HR‑governance (агрегатор). См. [hr-staff-governance.md](hr-staff-governance.md). |
| `hr_payroll` | Payroll. |
| `employee_records` | Кадровые записи. |
| `staff_recruitment` | Найм. |
| `staff_onboarding` | Онбординг. |
| `staff_exit_offboarding` | Офбординг. |
| `staff_probation_review` | Испытательный срок. |
| `performance_appraisal` | Аттестация. |
| `faculty_attestation` | Аттестация ППС. |
| `leave_management` | Отпуска. |
| `timesheet_management` | Табели. |
| `contracts_hr` | HR‑контракты. |
| `disciplinary_case_management` | Дисциплинарные кейсы. |
| `faculty` | Факультет/ППС. |
| `faculty_performance_kpis` | KPI ППС. |
| `faculty_copilot` | AI‑ассистент ППС. |

## 6. Кампус / Инфраструктура / Безопасность

| Модуль | Назначение |
|--------|-----------|
| `campus_facilities_housing_transport` | Кампус: здания, общежития, транспорт (агрегатор). См. [campus-facilities.md](campus-facilities.md). |
| `campus_sla` | SLA кампуса. |
| `facilities_work_orders` | Заявки на обслуживание. |
| `operations` | Операции (facility issues, work orders, cleaning, utilities). |
| `housing` | Общежития. |
| `dormitory_management` | Управление общежитиями. |
| `transport` | Транспорт. |
| `dining` | Питание. |
| `parking` | Парковка. |
| `parking_enforcement` | Контроль парковки. |
| `parking_permit_ops` | Пропуска на парковку. |
| `room_booking` | Бронирование аудиторий. |
| `equipment_booking` | Бронирование оборудования. |
| `lab_operations` | Операции лабораторий. |
| `events_management` | Управление событиями. |
| `event_registration_portal` | Портал регистрации на события. |
| `security_access_compliance` | Безопасность/доступ/соответствие (агрегатор). См. [security-access-compliance.md](security-access-compliance.md). |
| `security_operations` | Операции безопасности (инциденты). |
| `access_control` | Контроль доступа. |
| `visitor_management` | Управление посетителями. |

## 7. Исследования и инновации

| Модуль | Назначение |
|--------|-----------|
| `research_science` | Исследования (brain‑вертикаль). См. [research-science.md](research-science.md). |
| `research` | Исследования (гранты, публикации). |
| `research_projects` | Исследовательские проекты. |
| `research_ethics` | Этика исследований. |
| `research_grants` | Гранты. |
| `innovation_commercialization` | Инновации/коммерциализация IP. **Не закоммичен (P1).** |
| `ip_management` | Управление интеллектуальной собственностью. |
| `patents` | Патенты. |
| `publications` | Публикации. |
| `publication_registry` | Реестр публикаций. |
| `conference_management` | Управление конференциями. |
| `mou_lifecycle` | Жизненный цикл MoU. |
| `partnership_registry` | Реестр партнёрств. |
| `international_office` | Международный офис. |
| `inbound_exchange_management` | Входящие обмены. |
| `outbound_exchange_management` | Исходящие обмены. |

## 8. Качество, аккредитация, отчётность, governance

| Модуль | Назначение |
|--------|-----------|
| `quality_accreditation` | Качество/аккредитация (brain‑вертикаль, 8 под‑роутеров). См. [quality-accreditation.md](quality-accreditation.md). |
| `accreditation` | Аккредитация. |
| `accreditation_compliance` | Соответствие аккредитации. |
| `accreditation_dashboard` | Дашборд аккредитации. |
| `compliance_calendar_dashboard` | Календарь соответствия. |
| `reporting_runtime` | Регуляторная отчётность (Ministry brain, 8 сервисов). См. [../brains/reporting-ministry.md](../brains/reporting-ministry.md). |
| `ministry_reporting_dashboard` | Дашборд отчётности министерству. |
| `executive_governance` | Исполнительный governance (brain). См. [executive-governance.md](executive-governance.md). |
| `executive_control_tower` | Исполнительная «башня управления». |
| `rector_assignment_workflow` | Поручения ректора. |
| `rector_resolution_tracking_workflow` | Отслеживание резолюций ректора. |
| `rector_strategy_dashboard` | Стратегический дашборд ректора. |
| `committee_decision_registry` | Реестр решений комитетов. |
| `analytics` | Аналитика/BI. |

## 9. Документы / Корреспонденция

| Модуль | Назначение |
|--------|-----------|
| `document_decree_correspondence` | Документы/приказы/корреспонденция (агрегатор). См. [documents.md](documents.md). |
| `document_workflow_os` | Document management OS. |
| `document_workflow` | Маршрутизация документов. |
| `document_template_library` | Библиотека шаблонов. |
| `digital_documents` | Цифровые документы. |
| `digital_certificates` | Цифровые сертификаты. |
| `digital_signature_integration` | ЭЦП‑интеграция. |
| `order_decree_registry` | Реестр приказов/декретов. |
| `incoming_outgoing_correspondence` | Входящая/исходящая корреспонденция. |
| `records_hub` | Хаб записей. |
| `archive_retention_management` | Архив и хранение. |
| `blockchain_diploma` | Блокчейн‑дипломы. |
| `contracts_legal_repository` | Репозиторий юр. договоров. |

## 10. AI / Brain

| Модуль | Назначение |
|--------|-----------|
| `brain_core` | Ядро решений. См. [../brains/brain-core.md](../brains/brain-core.md). |
| `brain_decision_audit_trail` | Аудит‑трейл решений Brain. |
| `digital_twin` | Цифровой двойник. См. [../brains/digital-twin.md](../brains/digital-twin.md). |
| `ai_gateway` | AI‑шлюз (мультипровайдер). См. [ai.md](ai.md). |
| `ai_routing_control` | Маршрутизация AI. |
| `ai_cost_governance` | Управление стоимостью AI. |
| `ai_guardrails` | Ограничители AI. |
| `ai_copilot_ops` | Операции AI‑copilot. |
| `ai_plagiarism` | AI‑антиплагиат. |
| `knowledge_retrieval` | RAG/поиск знаний. |
| `prompt_management` | Управление промптами. |
| `model_evaluation` | Оценка моделей. |
| `safe_task_drafting_agent` | Safe‑агент черновиков задач (UCE‑146). |
| `safe_evidence_summary_agent` | Safe‑агент сводок доказательств (UCE‑145). |

## 11. Платформа / Инфраструктура / Auth

| Модуль | Назначение |
|--------|-----------|
| `platform` | Платформенный self‑service. См. [platform-core.md](platform-core.md). |
| `platform_shared` | Общие платформенные утилиты. |
| `platform_health` | Здоровье платформы. |
| `observability` | Логи/метрики/health/трейсинг. |
| `federation_management` | Федерация (мульти‑институт). |
| `feature_flags` | Feature flags. См. [../10_FEATURE_FLAGS.md](../10_FEATURE_FLAGS.md). |
| `jobs` | Фоновые задачи (очередь). |
| `workflows` | Движок workflow. |
| `backup` | Резервное копирование. |
| `audit` | Аудит‑лог. |
| `auth` | Аутентификация. См. [auth-identity.md](auth-identity.md). |
| `identity` | Управление идентичностью (OIDC). |
| `identity_provider_integration` | Интеграция IdP. |
| `ldap` | LDAP/AD. |
| `sso_saml` | SAML SSO. |
| `two_factor_auth` | 2FA. |
| `rbac` | RBAC/ABAC. См. [../03_ROLES_AND_RBAC.md](../03_ROLES_AND_RBAC.md). |
| `service_accounts` | Сервисные аккаунты. |
| `local_user_management` | Локальные пользователи. |
| `profiles` | Профили пользователей. |
| `tenants` | Тенанты. |
| `org_structure` | Оргструктура. |
| `i18n` | Интернационализация. |
| `help` | Справка. |
| `admin` | Админ‑агрегатор. |
| `developer_portal` | Портал разработчика. |
| `mobile_app` | Мобильное приложение (backend). |
| `mobile_push_gateway` | Push‑шлюз. |
| `notification_center` | Центр уведомлений. |
| `communications` | Коммуникации (brain). См. [communications.md](communications.md). |

## 12. Интеграции (country‑adapter, L2)

| Модуль | Назначение |
|--------|-----------|
| `integrations` | Управление провайдерами интеграций. |
| `integration_provider_readiness` | Готовность провайдеров интеграций. |
| `provider_readiness` | Готовность провайдеров (L4). |
| `finance_erp_integration` | ERP‑финансы. |
| `hr_payroll_integration` | HR/Payroll. |
| `payment_gateway_integration` | Платёжный шлюз. |
| `learning_management_system_integration` | LMS. |
| `student_information_system_integration` | SIS. |
| `government_services_integration` | Госсервисы. |
| `regulatory_reporting_integration` | Регуляторная отчётность. |
| `notification_gateway_integration` | Шлюз уведомлений. |
| `email_gateway_integration` | Email‑шлюз. |
| `expansion_visibility` | Видимость расширения (L4). |

## 13. Комплаенс / Приватность / Риски

| Модуль | Назначение |
|--------|-----------|
| `pdpl` | PDPL (защита перс. данных). |
| `consent_management_policy` | Управление согласиями. |
| `data_retention_policy_control` | Политики хранения данных. |
| `third_party_risk_policy` | Риски третьих сторон. |
| `library` | Библиотека. |
| `library_circulation` | Библиотечная циркуляция. |

> **Итого:** каждый backend‑модуль охвачен. Frontend‑модули соответствуют доменам (см. [../pages/README.md](../pages/README.md)). Проблемы дубликатов/незакоммиченного кода — в [../02_MODULE_DEPENDENCY_MAP.md](../02_MODULE_DEPENDENCY_MAP.md) §3.6.
