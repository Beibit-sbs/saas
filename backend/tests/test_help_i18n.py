from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def test_help_topics_endpoint() -> None:
    response = client.get("/api/help/topics")
    assert response.status_code == 200
    assert "topics" in response.json()


def test_help_ask_endpoint() -> None:
    client.cookies.clear()
    payload = {
        "page": "admin",
        "question": "Как добавить роль?",
        "field": "role_name",
        "language": "ru",
    }
    response = client.post("/api/help/ask", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "next_steps" in body


def test_help_ask_endpoint_english() -> None:
    client.cookies.clear()
    payload = {
        "page": "admin",
        "question": "How to add a role?",
        "field": "role_name",
        "language": "en",
    }
    response = client.post("/api/help/ask", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["context"]["language"] == "en"


def test_public_languages_endpoint() -> None:
    response = client.get("/api/i18n/languages")
    assert response.status_code == 200
    body = response.json()
    assert "languages" in body
    codes = {item["code"] for item in body["languages"]}
    assert {"kk", "ru", "en"}.issubset(codes)


def test_public_language_catalog_endpoint() -> None:
    response = client.get("/api/i18n/catalog")
    assert response.status_code == 200
    body = response.json()
    assert "languages" in body
    codes = {item["code"] for item in body["languages"]}
    assert {"kk", "ru", "en", "zh", "hi", "de"}.issubset(codes)


def test_admin_add_language_endpoint() -> None:
    payload = {
        "code": "zh",
        "name": "Chinese",
        "native_name": "中文",
    }
    response = client.post("/api/admin/i18n/languages", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["language"]["code"] == "zh"


def test_admin_disable_custom_language_endpoint() -> None:
    client.post(
        "/api/admin/i18n/languages",
        json={"code": "zh", "name": "Chinese", "native_name": "中文"},
        headers=ADMIN_HEADERS,
    )

    response = client.patch(
        "/api/admin/i18n/languages/zh",
        json={"enabled": False},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"]["code"] == "zh"
    assert body["language"]["enabled"] is False


def test_admin_cannot_disable_system_language() -> None:
    response = client.patch(
        "/api/admin/i18n/languages/ru",
        json={"enabled": False},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 400


def test_admin_delete_custom_language_endpoint() -> None:
    client.post(
        "/api/admin/i18n/languages",
        json={"code": "zh", "name": "Chinese", "native_name": "中文"},
        headers=ADMIN_HEADERS,
    )

    response = client.delete("/api/admin/i18n/languages/zh", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_admin_cannot_delete_system_language() -> None:
    response = client.delete("/api/admin/i18n/languages/en", headers=ADMIN_HEADERS)
    assert response.status_code == 400


def test_profile_language_preference_requires_user_id() -> None:
    client.cookies.clear()
    response = client.get("/api/auth/me/preferences")
    assert response.status_code == 401


def test_profile_language_preference_set_and_get() -> None:
    headers = _auth_headers("student.001", ["student"])

    set_response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "en"},
        headers=headers,
    )
    assert set_response.status_code == 200
    assert set_response.json()["language"] == "en"

    get_response = client.get("/api/auth/me/preferences", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["language"] == "en"


def test_profile_language_preference_rejects_disabled_language() -> None:
    headers = _auth_headers("student.002", ["student"])

    client.post(
        "/api/admin/i18n/languages",
        json={"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
        headers=ADMIN_HEADERS,
    )
    client.patch(
        "/api/admin/i18n/languages/hi",
        json={"enabled": False},
        headers=ADMIN_HEADERS,
    )

    response = client.put(
        "/api/auth/me/preferences/language",
        json={"language": "hi"},
        headers=headers,
    )
    assert response.status_code == 400
