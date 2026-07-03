# Frontend Alignment — Progress Tracker

Source of truth priority: `docs-audit/` > `A-050–A-056` > Backend > Frontend.
Backend / API / business logic are **not** modified. Frontend is aligned to match.
Modules processed strictly in `docs-audit/modules/` (alphabetical) order.

| # | Модуль | Готовность | Build | TS | ESLint | QA | Статус |
|---|--------|-----------:|:-----:|:--:|:------:|:--:|--------|
| 1 | Academic Operations | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 2 | Admissions | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 3 | AI | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 4 | Auth / Identity | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 5 | Campus Facilities | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 6 | Communications | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 7 | Documents | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 8 | Executive Governance | 100% | ✅ | ✅ | ✅ | ✅ | Done |
| 9 | Finance / Procurement / Asset | 0% | — | — | — | — | Pending |
| 10 | HR / Staff Governance | 0% | — | — | — | — | Pending |
| 11 | Platform Core | 0% | — | — | — | — | Pending |
| 12 | Quality Accreditation | 100% | ✅ | ✅ | ✅ | ⏳ | Code-aligned (pre-pipeline) |
| 13 | Research Science | 0% | — | — | — | — | Pending |
| 14 | Scheduling Timetable | 0% | — | — | — | — | Pending |
| 15 | Security Access Compliance | 0% | — | — | — | — | Pending |
| 16 | Student Lifecycle | 0% | — | — | — | — | Pending |
| 17 | Student Success | 100% | ✅ | ✅ | ✅ | ⏳ | Code-aligned (pre-pipeline) |

Legend: ✅ pass · ⏳ in progress/pending verification · — not started.

> Note: modules 6/12/17 were code-aligned in an earlier pass (real API, tsc clean, no mocks) but predate this formal Functional-QA pipeline; they will receive a full browser QA pass when reached in order.

> **Global fix (module 4):** wiring `adminTranslations` into `LanguageProvider` fixed raw i18n keys on ALL admin pages that use admin-only translation keys — this retroactively benefits every admin module, not just Auth.

_Last updated: 2026-07-03 (after Executive Governance module functional QA)._
