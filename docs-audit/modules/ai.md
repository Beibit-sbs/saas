# Модуль: AI Gateway и AI‑слой

[← Каталог модулей](README.md) · [Индекс](../README.md)

Backend: `ai_gateway/`, `ai_routing_control/`, `ai_cost_governance/`, `ai_guardrails/`, `ai_copilot_ops/`, `ai_plagiarism/`, `ai_admissions_scoring/`, `knowledge_retrieval/`, `prompt_management/`, `model_evaluation/`, `faculty_copilot/`, `student_ai_tutor/`, `safe_task_drafting_agent/`, `safe_evidence_summary_agent/`
Frontend: `frontend/modules/ai-cost/`, `ai-routing/`, `brain-core/`, `faculty-copilot/`, `knowledge-retrieval/`, `prompt-management/`, `model-evaluation/`
Вертикаль: **V17 AI** (в связке с Brain Core)

## Назначение
AI‑инфраструктура платформы: единый шлюз к LLM‑провайдерам, маршрутизация, контроль стоимости, guardrails, RAG, промпты, оценка моделей, copilot'ы, safe‑агенты.

## Бизнес‑функции
Реестр моделей · единый `POST /api/ai/chat` · usage‑логирование · маршрутизация/стоимость · guardrails · RAG (knowledge retrieval) · prompt lifecycle · model evaluation · faculty copilot · AI‑tutor · AI‑плагиат · admissions scoring · safe drafting/evidence агенты.

## Пользователи (роли)
`platform_admin`, доменные admin'ы (copilot), faculty (copilot), student (tutor); `auditor`.

## Страницы
`/console/ai/*` (root, brain, brain/policy, brain/intelligence, copilot, cost, routing), `/console/knowledge-retrieval`, `/console/prompt-management`, `/console/model-evaluation`, `/console/faculty-copilot`.

## Backend
- **Router:** `ai_gateway/router.py` (+ `public_router.py`), `faculty_copilot`, `knowledge_retrieval`, `prompt_management`, `model_evaluation`.
- **Services:** адаптеры провайдеров, usage‑логгер.

## Database
`model_eval_runs`, `prompt_templates`, `knowledge_retrieval_documents`; AI Gateway registry/usage таблицы (миграция `f2b6d4a9c8e1_add_ai_gateway_v1_registry_and_usage`, частично RLS).

## API
`/api/admin/ai`, `/api/ai/chat` (public), `/api/admin/knowledge-retrieval`, `/api/admin/prompt-management`, `/api/admin/model-evaluation`, `/api/admin/faculty-copilot`. Permission `ai.chat.execute` и др.

## Провайдеры
OpenAI, Gemini, Anthropic, custom (Ollama/deepseek‑r1 опционально). Ключи: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `AI_CUSTOM_PROVIDER_URL/API_KEY`.

## Связанные модули
`brain_core` (reasoning/ai_adapter, ExplanationEngine, llm_bridge), `ai_admissions_scoring`, `ai_plagiarism`, все домены (copilot).

## Brain / AI
Является AI‑подложкой Brain Core. Safe‑агенты (`safe_task_drafting_agent` UCE‑146, `safe_evidence_summary_agent` UCE‑145) — `RUNTIME_EXECUTION_ALLOWED=False`, human‑gated.

## Проблемы / Рекомендации
- Граница интеграции `llm_bridge` не полностью прослежена в статике. Много AI‑модулей — риск фрагментации. **Рекомендация:** документировать LLM‑bridge, консолидировать AI‑governance (cost/routing/guardrails).
