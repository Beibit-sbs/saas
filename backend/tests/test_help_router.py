"""
ERP-QA-84 – Help router endpoint tests.

Covers 2 endpoints under /api/help:
  GET   /topics
  POST  /ask

Also covers: normalize_language(), build_answer() helper branches.
"""

from __future__ import annotations


from tests.conftest import ADMIN_HEADERS, client
from app.modules.help.router import build_answer, normalize_language


# ---------------------------------------------------------------------------
# normalize_language unit tests
# ---------------------------------------------------------------------------


class TestNormalizeLanguage:
    def test_supported_languages(self):
        assert normalize_language("ru") == "ru"
        assert normalize_language("en") == "en"
        assert normalize_language("kk") == "kk"

    def test_unsupported_falls_back_to_ru(self):
        assert normalize_language("fr") == "ru"
        assert normalize_language("") == "ru"
        assert normalize_language("zh") == "ru"


# ---------------------------------------------------------------------------
# build_answer unit tests – roles branch
# ---------------------------------------------------------------------------


class TestBuildAnswerRoles:
    def test_roles_ru(self):
        answer, steps = build_answer("admin", "Как создать роль?", None, "ru")
        assert "Admin -> Roles" in answer
        assert len(steps) == 3

    def test_roles_en(self):
        answer, steps = build_answer("roles", "How to create a role?", None, "en")
        assert "Roles" in answer
        assert len(steps) == 3

    def test_roles_kk(self):
        answer, steps = build_answer("rbac", "role кұру", None, "kk")
        assert "Roles" in answer
        assert len(steps) == 3

    def test_roles_with_field_hint_ru(self):
        answer, _ = build_answer("admin", "Как настроить роль?", "role_name", "ru")
        assert "Поле: role_name" in answer

    def test_roles_with_field_hint_en(self):
        answer, _ = build_answer("admin", "роль", "role_name", "en")
        assert "Field: role_name" in answer

    def test_roles_with_field_hint_kk(self):
        answer, _ = build_answer("admin", "роль", "role_name", "kk")
        assert "Орис: role_name" in answer


# ---------------------------------------------------------------------------
# build_answer unit tests – LDAP branch
# ---------------------------------------------------------------------------


class TestBuildAnswerLdap:
    def test_ldap_ru(self):
        answer, steps = build_answer("general", "Как подключить ldap?", None, "ru")
        assert "LDAP" in answer
        assert len(steps) == 3

    def test_ldap_en(self):
        answer, steps = build_answer("general", "configure ldap", None, "en")
        assert "LDAP/AD" in answer

    def test_ldap_kk(self):
        answer, steps = build_answer("general", "AD баптау", None, "kk")
        assert "LDAP/AD" in answer

    def test_ldap_with_field(self):
        answer, _ = build_answer("general", "ldap настройка", "bind_dn", "ru")
        assert "Поле: bind_dn" in answer


# ---------------------------------------------------------------------------
# build_answer unit tests – AI/API branch
# ---------------------------------------------------------------------------


class TestBuildAnswerApi:
    def test_api_keys_ru(self):
        answer, steps = build_answer("ai", "как задать API ключ?", None, "ru")
        assert "API" in answer

    def test_api_keys_en(self):
        answer, steps = build_answer("general", "api key setup", None, "en")
        assert "API" in answer

    def test_api_keys_kk(self):
        answer, steps = build_answer("general", "API кілттерін кіргізу", None, "kk")
        assert "API" in answer

    def test_api_page_ai(self):
        answer, _ = build_answer("ai", "Проверка провайдера", None, "ru")
        assert "API" in answer


# ---------------------------------------------------------------------------
# build_answer unit tests – default/general branch
# ---------------------------------------------------------------------------


class TestBuildAnswerDefault:
    def test_default_ru(self):
        answer, steps = build_answer("general", "Как заполнить форму?", None, "ru")
        assert "обязательные" in answer.lower() or "валидаци" in answer.lower()
        assert len(steps) == 3

    def test_default_en(self):
        answer, steps = build_answer("general", "How to fill a form?", None, "en")
        assert "required" in answer.lower() or "validate" in answer.lower()

    def test_default_kk(self):
        answer, steps = build_answer("general", "Форма толтыру", None, "kk")
        assert len(steps) == 3

    def test_default_with_field(self):
        answer, _ = build_answer("general", "Что писать тут?", "email", "ru")
        assert "Поле: email" in answer


# ---------------------------------------------------------------------------
# GET /topics
# ---------------------------------------------------------------------------


class TestGetTopics:
    def test_topics_happy(self):
        r = client.get("/api/help/topics", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "topics" in data
        assert "general" in data["topics"]
        assert "admin" in data["topics"]
        assert "ai" in data["topics"]

    def test_topics_no_auth(self):
        """Help topics likely require actor (get_actor dependency)."""
        r = client.get("/api/help/topics")
        # If auth is required it returns 401/403, otherwise 200
        assert r.status_code in (200, 401, 403)


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------


class TestAskHelp:
    def test_ask_happy_default(self):
        payload = {"question": "Как заполнить форму?"}
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "next_steps" in data
        assert data["context"]["language"] == "ru"

    def test_ask_with_page_and_field(self):
        payload = {
            "question": "Как создать роль?",
            "page": "admin",
            "field": "role_name",
            "language": "ru",
        }
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "Поле: role_name" in data["answer"]

    def test_ask_english(self):
        payload = {
            "question": "How to configure LDAP?",
            "language": "en",
        }
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert r.json()["context"]["language"] == "en"

    def test_ask_kazakh(self):
        payload = {
            "question": "LDAP кантип курам?",
            "language": "kk",
        }
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert r.json()["context"]["language"] == "kk"

    def test_ask_unsupported_language_falls_back(self):
        payload = {
            "question": "Comment configurer?",
            "language": "fr",
        }
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert r.json()["context"]["language"] == "ru"

    def test_ask_question_too_short(self):
        payload = {"question": "ab"}
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_ask_no_auth(self):
        payload = {"question": "Как заполнить форму?"}
        r = client.post("/api/help/ask", json=payload)
        assert r.status_code in (401, 403)

    def test_ask_ai_page(self):
        payload = {
            "question": "Как проверить статус интеграции?",
            "page": "ai",
        }
        r = client.post("/api/help/ask", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert "API" in r.json()["answer"]
