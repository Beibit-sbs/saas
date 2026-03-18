# Первый Запрос Для Нового Проекта

После того как скопировал шаблон в новую папку и открыл ее в VS Code, вставь в чат этот запрос.

## Полная версия
```text
Use .ai/master-orchestrator.md.

Build system:
- Name: <название проекта>
- Goal: <какую систему нужно создать>
- Users and roles: <кто будет пользоваться системой>
- Core modules: <главные модули>
- Required features: <обязательные функции>
- Integrations: <если нужны внешние сервисы>
- Data sensitivity (personal data yes/no): <yes/no>
- Auth requirements: <логин, роли, права доступа>
- LDAP/AD requirements: <как подключаем AD, группы и роли>
- Admin dashboard requirements: <какие разделы обязательны>
- AI provider requirements (OpenAI/Gemini/other): <каких провайдеров подключить>
- Non-functional requirements: <аудит, производительность, надежность>
- Deployment target: <local/staging/prod>
- Deadline or phase target: <MVP / этап / срок>

Run Architect -> Developer -> Reviewer -> Security -> DevOps.
Stop only at approval gates.
Follow .ai/rules.md.
```

## Короткая версия
```text
Use .ai/master-orchestrator.md.
Build a browser-based system for <описание системы>.
Run Architect -> Developer -> Reviewer -> Security -> DevOps.
Stop only at approval gates.
```

## Что произойдет дальше
1. AI сначала предложит архитектуру.
2. Потом спросит подтверждение архитектуры.
3. После этого перейдет к плану реализации.
4. Затем выполнит review, security и devops-этапы.
5. В конце отдаст готовый пакет для запуска и деплоя.

## Как отвечать на gate-вопросы
- Если все подходит: `yes`
- Если нужно исправить: `no` и коротко напиши, что изменить