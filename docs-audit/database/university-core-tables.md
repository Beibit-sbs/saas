# Кластер таблиц: University Core

[← Каталог таблиц](README.md) · Модуль: [../modules/student-lifecycle.md](../modules/student-lifecycle.md), [../modules/academic-operations.md](../modules/academic-operations.md)

Ядровые академические сущности. Реестр — `university_core/shared.py`; ORM — `students/`, `faculty/`, `programs/`, `courses/`, `enrollments/`, `academic_records/`.

## Основные таблицы

| Таблица | Описание | Модуль | PK | FK | CRUD |
|---------|----------|--------|----|----|------|
| `university_students` | Студенты | students | id | tenant_id→app_tenants | students |
| `university_faculty` | ППС/преподаватели | faculty | id | tenant_id | faculty |
| `university_faculty_contracts` | Контракты ППС | faculty | id | tenant_id, faculty_id | faculty |
| `university_programs` | Образовательные программы | programs | id | tenant_id | programs |
| `university_courses` | Курсы | courses | id | tenant_id | courses |
| `university_course_prerequisites` | Пререквизиты курсов | courses | id | tenant_id, course_id | courses/prereq |
| `university_enrollments` | Зачисления (enum EnrollmentStatus/Type) | enrollments | id | tenant_id, student_id, section/term | enrollments |
| `university_academic_records` | Академические записи | academic_records | id | tenant_id, student_id | academic_records, registrar |
| `app_transcripts` / `app_transcript_items` | Транскрипты | transcripts | id | tenant_id, student_id | transcripts |

## Связи
`students` 1:N `enrollments`; `programs` 1:N `courses` (косвенно), `courses` 1:N `prerequisites`; `faculty` 1:N `faculty_contracts`; `students` 1:N `academic_records` 1:N `transcript_items`.

## Индексы
`tenant_id` (все); композитные unique с `tenant_id` для изоляции (напр. enrollments `(tenant_id, student_id, section_id)`).

## Enum / справочники
`EnrollmentStatus` (PENDING/ENROLLED/WAITLIST/DROPPED/COMPLETED/WITHDRAWN/SUSPENDED), `EnrollmentType` (REGULAR/AUDIT/RETAKE/TRANSFER_CREDIT).

## Используется в
academic_operations, student_lifecycle, student_success, grades, degree_progress, scheduling, admissions (target program), Brain Core (context academic).

## Alert‑спутники
`university_program_sunset_alerts`, `university_course_retirement_alerts`, `university_academic_withdrawal_alerts`, `university_faculty_contract_termination_alerts` — см. [alert-tables.md](alert-tables.md).
