# Wave 1 Prep Design Brief: #22 Faculty Workload Planning

Дата: 2026-04-18
Task ID: #22
Статус: PREP-OPEN
Owner: Academic Domain Team
Reviewers: Backend Lead, Scheduling Team

## 1) Контекст и цель

Faculty profile (CRUD) и Scheduling (sections, instructor assignments, classrooms) уже работают в production. Но нет вычисления нагрузки преподавателя, лимитов, и fairness-правил. Текущий `faculty.workload_index` в semantic layer — прокси (grades volume / students), не настоящий workload.

## 2) Текущее состояние (as-is)

### Faculty модуль (330 LOC):
- `FacultyModel`: faculty_id, first_name, last_name, department, email, status, tenant_id
- CRUD через `tenant_entity_service` + `get_faculty_consistency_report()`
- **Нет:** rank/title, max_credit_hours, contract_type, fte_ratio, hire_date

### Scheduling модуль (2958 LOC):
- `CourseSectionModel`: course_id, term_id, instructor_id, max_capacity, status
- `InstructorAssignmentModel`: instructor_id (string!), section_id, role (primary/assistant)
- `business_rules.py`: validate_no_instructor_conflict (schedule collision), validate_classroom_capacity
- **Нет:** workload calculation, teaching load limits

### Courses модуль (313 LOC):
- `CourseModel`: course_code, title, **credits** (int), program_id, status, tenant_id
- Credits поле существует, но нигде не используется для расчёта нагрузки

### Ключевой architectural gap:
- `InstructorAssignmentModel.instructor_id` — **свободная строка**, не FK на `FacultyModel`
- Нет validated join между faculty и instructor assignments

## 3) Целевое состояние (to-be, post-day7)

### 3.1 Расширение Faculty Model

```python
# Новые поля в FacultyModel:
rank: str               # "professor", "associate", "assistant", "adjunct", "lecturer"
contract_type: str      # "full_time", "part_time", "visiting", "emeritus"
fte_ratio: float        # 0.0 – 1.0 (1.0 = полная ставка)
max_credit_hours: int   # лимит credit-hours per term (default по contract_type)
hire_date: date | None
specializations: list[str]  # JSON array
```

### 3.2 FK Validated Join

- `InstructorAssignmentModel.instructor_id` → validated against `FacultyModel.faculty_id`
- Migration: добавить FK constraint с `SET NULL` для legacy unlinked records
- Fallback: если instructor_id не найден в faculty, assignment всё равно работает (warn, не block)

### 3.3 Workload Calculation Service

```python
class FacultyWorkloadService:
    def get_workload(faculty_id, term_id) -> FacultyWorkload:
        """
        Для каждого faculty:
        1. Найти InstructorAssignments (role=primary) для term_id
        2. Для каждой section → course → credits
        3. SUM credits = total_credit_hours
        4. Compare vs max_credit_hours → utilization %
        """

    def get_department_workload_summary(department, term_id) -> list[FacultyWorkload]:
        """Summary по кафедре с fairness metrics."""
```

### 3.4 Business Rules

| Rule | Описание | Action |
|------|----------|--------|
| `max_credit_exceeded` | total > max_credit_hours | WARN (soft limit) |
| `overload_threshold` | total > 1.25 × max_credit_hours | BLOCK assignment |
| `underload_alert` | total < 0.5 × max_credit_hours | INFO (кафедре) |
| `fairness_check` | std_dev(utilization) > threshold in department | WARN |

### 3.5 API Contract (draft)

Prefix: `/api/admin/faculty`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/{faculty_id}/workload?term_id=` | Workload для одного преподавателя |
| `GET` | `/workload/department/{department}?term_id=` | Summary по кафедре |
| `GET` | `/workload/alerts?term_id=` | Overload/underload alerts |
| `PUT` | `/{faculty_id}/capacity` | Обновить max_credit_hours / fte_ratio |

### 3.6 Semantic Layer Update

Заменить proxy `faculty.workload_index` реальным расчётом:
```python
# Вместо: total_grades / max(total_students, 1)
# Будет: SUM(course.credits * section.status='active') / max_credit_hours
```

## 4) Data Model (draft)

### Расширение FacultyModel (Alembic migration):
```sql
ALTER TABLE app_faculty
  ADD COLUMN rank VARCHAR(32) DEFAULT 'lecturer',
  ADD COLUMN contract_type VARCHAR(32) DEFAULT 'full_time',
  ADD COLUMN fte_ratio NUMERIC(3,2) DEFAULT 1.00,
  ADD COLUMN max_credit_hours INTEGER DEFAULT 18,
  ADD COLUMN hire_date DATE,
  ADD COLUMN specializations JSONB DEFAULT '[]';
```

### FK constraint (мягкий, с fallback):
```sql
-- Не добавляем жёсткий FK, т.к. instructor_id — свободная строка
-- Вместо этого: validated join в service layer
CREATE INDEX idx_instructor_assignment_faculty
  ON app_instructor_assignments (instructor_id);
```

## 5) Skeleton Test List

Backend:
- `test_faculty_workload_returns_credit_sum_for_term`
- `test_faculty_workload_respects_primary_assistant_role`
- `test_faculty_workload_overload_returns_alert`
- `test_faculty_workload_underload_returns_alert`
- `test_department_workload_summary_includes_all_faculty`
- `test_department_fairness_flag_on_high_std_dev`
- `test_workload_with_unlinked_instructor_id_returns_zero`
- `test_update_capacity_persists_max_credit_hours`
- `test_semantic_workload_index_uses_real_calculation`

Frontend:
- `test_faculty_workload_page_renders`
- `test_faculty_workload_shows_utilization_bar`
- `test_department_summary_table_renders`

## 6) Execution Priority (post-day7)

| Шаг | Компонент | Приоритет | Зависимости |
|-----|-----------|-----------|-------------|
| 1 | Faculty model extension (migration) | P0 | Нет |
| 2 | Workload calculation service | P0 | Шаг 1 |
| 3 | Business rules (limits, alerts) | P0 | Шаг 2 |
| 4 | API endpoints | P0 | Шаг 2-3 |
| 5 | Semantic layer update | P1 | Шаг 2 |
| 6 | Frontend UI | P1 | F3.4 Frontend wave + Шаг 4 |
| 7 | Department fairness rules | P2 | Шаг 2 |

## 7) Риски и ограничения

1. **instructor_id → faculty_id mapping** — не у всех assignments будет match. Нужен migration script для linking.
2. **Credit calculation** — зависит от наличия `credits` в `CourseModel` (есть) и корректной привязки course → section.
3. **Term boundaries** — нужна чёткая привязка к `term_id` для корректных расчётов per-semester.
4. **Backwards compatibility** — старые assignments без faculty_id link продолжают работать (soft check).

## 8) Definition of Done (для перехода #22 из PLANNED → EXISTS)

- [ ] Faculty model расширен (rank, contract_type, fte_ratio, max_credit_hours)
- [ ] Workload calculation service с credit sum per term
- [ ] Business rules: overload/underload alerts
- [ ] ≥4 API endpoints
- [ ] Semantic layer uses real workload calculation
- [ ] Frontend: workload page с utilization view
- [ ] Regression: все faculty/scheduling тесты green
- [ ] Coverage: ≥80% на новый код
