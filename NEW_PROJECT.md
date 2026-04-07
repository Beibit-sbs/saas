# Чеклист Нового Проекта

Используй этот репозиторий-шаблон как базу для каждого нового продукта.

## 1. Скопируй шаблон
```bash
cd /home/sbs
cp -a AI my-new-project
```

## 2. Сбрось git-историю для нового проекта
```bash
cd /home/sbs/my-new-project
rm -rf .git
git init
```

## 3. Открой новый проект в VS Code
```bash
code /home/sbs/my-new-project
```

## 4. Подготовь окружение
```bash
cp infra/.env.example infra/.env
./scripts/bootstrap.sh
```

Важно:
- demo users и demo auth paths в шаблоне предназначены только для template/demo использования;
- перед production launch их нужно отключить, удалить или заменить;
- это обязательная проверка для каждого производного проекта.

## 5. Зафиксируй контекст проекта
Скопируй шаблон контекста и заполни его перед первой большой задачей:

```bash
cp docs/templates/project-context-template.md PROJECT_CONTEXT.md
```

Минимум для заполнения:
- границы проекта (in/out of scope),
- роли пользователей,
- требования по LDAP/AD и RBAC,
- требования к данным и безопасности,
- интеграции и ограничения.

## 5.1 Проверь baseline шаблона
Перед началом продуктовой разработки зафиксируй, что шаблон в новом проекте стартует без регрессий:

```bash
make pipeline
```

Что должно быть на выходе:
- тесты backend проходят,
- frontend i18n parity check проходит,
- frontend lint/build проходят,
- docker-стек поднимается,
- health endpoint доступен.

Важно: host-native npm/python dev workflow не используется; baseline проверяется только через Docker.

Считай baseline корректным, если `make pipeline` завершился без ошибок (`EXIT:0`).

## 6. Запусти AI-процесс разработки
Используй такой запрос:

```text
Use .ai/master-orchestrator.md.
Build system:
- Name: My New Project
- Goal: ...
- Users and roles: ...
- Core modules: ...
- Required features: ...
- Integrations: ...
- Data sensitivity (personal data yes/no): yes/no
- Auth requirements: ...
- LDAP/AD requirements: ...
- Admin dashboard requirements: ...
- AI provider requirements (OpenAI/Gemini/other): ...
- Non-functional requirements: ...
- Deployment target: staging/prod
- Deadline or phase target: ...
```

Готовая шпаргалка с первым запросом лежит в `FIRST_PROMPT.md`.

## Важное правило
- Держи `/home/sbs/AI` как мастер-шаблон.
- Вся продуктовая работа должна идти только внутри скопированных папок проекта.
- У каждого скопированного проекта должен быть свой `.git`-репозиторий.
- Demo auth surface нельзя переносить в production без явного пересмотра и замены.