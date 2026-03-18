from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/api/help", tags=["help"])


TOPICS = {
    "general": [
        "Как заполнить форму",
        "Что писать в обязательных полях",
        "Куда сохраняются изменения",
    ],
    "admin": [
        "Как добавить роль",
        "Как назначить права",
        "Как подключить LDAP/AD",
    ],
    "ai": [
        "Как добавить API ключ провайдера",
        "Как выбрать OpenAI/Gemini",
        "Как проверить статус интеграции",
    ],
}


class HelpQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    page: str = Field(default="general", max_length=120)
    field: str | None = Field(default=None, max_length=120)
    language: str = Field(default="ru", max_length=5)


def normalize_language(language: str) -> str:
    if language in {"kk", "ru", "en"}:
        return language
    return "ru"


def build_answer(page: str, question: str, field: str | None, language: str) -> tuple[str, list[str]]:
    lang = normalize_language(language)
    page_key = page.strip().lower()
    if lang == "en":
        field_hint = f" Field: {field}." if field else ""
    elif lang == "kk":
        field_hint = f" Орис: {field}." if field else ""
    else:
        field_hint = f" Поле: {field}." if field else ""

    if "роль" in question.lower() or page_key in {"admin", "roles", "rbac"}:
        if lang == "en":
            return (
                "Open Admin -> Roles, create a role, and assign permissions from the RBAC matrix." + field_hint,
                [
                    "Review docs/templates/rbac-matrix.md",
                    "Use permission checks, not hardcoded role names",
                    "Verify role changes in audit logs",
                ],
            )
        if lang == "kk":
            return (
                "Admin -> Roles болимине кириныз, role курып, RBAC матрицасы бойынша permissions берыныз." + field_hint,
                [
                    "docs/templates/rbac-matrix.md файлын караныз",
                    "Role атауына емес, permissions бойынша тексеру колданыныз",
                    "Role озгеристерин аудит журналынан тексериниз",
                ],
            )
        return (
            "Для настройки ролей открой раздел Admin -> Roles, создай роль и назначь permissions по матрице RBAC." + field_hint,
            [
                "Проверь шаблон docs/templates/rbac-matrix.md",
                "Назначай доступ через permissions, не через hardcode имен ролей",
                "Проверь аудит изменения роли",
            ],
        )

    if "ldap" in question.lower() or "ad" in question.lower():
        if lang == "en":
            return (
                "LDAP/AD is configured via env and backend adapter. Provide bind account, base DN, and group-to-role mapping." + field_hint,
                [
                    "Fill LDAP variables in infra/.env",
                    "Review docs/templates/ldap-ai-security-checklist.md",
                    "Use least-privileged service account",
                ],
            )
        if lang == "kk":
            return (
                "LDAP/AD env жане backend adapter аркылы бапталады. Bind account, base DN жане топ-роль mapping корсетиниз." + field_hint,
                [
                    "infra/.env ишинде LDAP айнымалыларын толтырыныз",
                    "docs/templates/ldap-ai-security-checklist.md тексериниз",
                    "Service account ушин minimum permissions бериниз",
                ],
            )
        return (
            "Подключение LDAP/AD настраивается через env и backend adapter. Укажи bind account, base DN и mapping групп к ролям." + field_hint,
            [
                "Заполни LDAP переменные в infra/.env",
                "Проверь checklist docs/templates/ldap-ai-security-checklist.md",
                "Ограничь права service account",
            ],
        )

    if "api" in question.lower() or "ключ" in question.lower() or page_key == "ai":
        if lang == "en":
            return (
                "AI provider API keys must be stored in env/secret manager and used via backend AI Gateway." + field_hint,
                [
                    "Set keys in infra/.env",
                    "Check /api/admin/ai/providers",
                    "Never keep keys in source code or git",
                ],
            )
        if lang == "kk":
            return (
                "AI провайдер API кілттери тек env/secret manager аркылы сакталуы керек, колдану backend AI Gateway аркылы жасалады." + field_hint,
                [
                    "infra/.env ишинде кілттерди толтырыныз",
                    "/api/admin/ai/providers аркылы статусын тексериниз",
                    "Кілттерди кодта немесе git-те сактамаңыз",
                ],
            )
        return (
            "API ключи AI-провайдеров задаются только через env/secret manager и используются через AI Gateway backend-модуль." + field_hint,
            [
                "Заполни ключи в infra/.env",
                "Проверь /api/admin/ai/providers",
                "Не храни ключи в коде и git",
            ],
        )

    if lang == "en":
        return (
            "Fill required fields by business meaning, then validate and save. If unsure, use docs/templates guides." + field_hint,
            [
                "Check fields against module requirements",
                "Validate required fields and formats",
                "Save and verify through API/UI",
            ],
        )
    if lang == "kk":
        return (
            "Минддетти орістерди бизнес-мағынасы бойынша толтырыныз, валидацияны тексерип, сактаңыз. Күмән болса docs/templates колданыңыз." + field_hint,
            [
                "Ористерди модуль талаптарымен салыстырыныз",
                "Минддетти орістер мен форматтарды тексериниз",
                "Сактап, натижени API/UI аркылы тексериниз",
            ],
        )
    return (
        "Заполни обязательные поля по бизнес-смыслу, затем проверь валидацию и сохрани. При сомнении используй шаблоны в docs/templates." + field_hint,
        [
            "Сверь поля с требованиями модуля",
            "Проверь обязательные поля и форматы",
            "Сохрани и проверь результат через API/интерфейс",
        ],
    )


@router.get("/topics")
def get_help_topics() -> dict[str, dict[str, list[str]]]:
    return {"topics": TOPICS}


@router.post("/ask")
def ask_help(payload: HelpQuestion) -> dict[str, object]:
    answer, next_steps = build_answer(
        payload.page,
        payload.question,
        payload.field,
        payload.language,
    )
    return {
        "answer": answer,
        "next_steps": next_steps,
        "context": {
            "page": payload.page,
            "field": payload.field,
            "language": normalize_language(payload.language),
        },
    }
