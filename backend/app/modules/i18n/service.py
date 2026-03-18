import re
import os
from dataclasses import dataclass

try:
    import psycopg
except ImportError:  # pragma: no cover - handled by fallback mode
    psycopg = None


@dataclass
class LanguageEntry:
    code: str
    name: str
    native_name: str
    enabled: bool
    system: bool


LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2,8}(-[a-z]{2,8})?$")


languages: dict[str, LanguageEntry] = {
    "kk": LanguageEntry(code="kk", name="Kazakh", native_name="Қазақша", enabled=True, system=True),
    "ru": LanguageEntry(code="ru", name="Russian", native_name="Русский", enabled=True, system=True),
    "en": LanguageEntry(code="en", name="English", native_name="English", enabled=True, system=True),
}

LANGUAGE_CATALOG: list[dict[str, str]] = [
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "it", "name": "Italian", "native_name": "Italiano"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "kk", "name": "Kazakh", "native_name": "Қазақша"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "ky", "name": "Kyrgyz", "native_name": "Кыргызча"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
    {"code": "tr", "name": "Turkish", "native_name": "Türkçe"},
    {"code": "uz", "name": "Uzbek", "native_name": "O'zbek"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"},
]


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _ensure_schema_and_seed(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_languages (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                native_name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                system BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        cur.executemany(
            """
            INSERT INTO app_languages(code, name, native_name, enabled, system)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO NOTHING
            """,
            [
                ("kk", "Kazakh", "Казакша", True, True),
                ("ru", "Russian", "Русский", True, True),
                ("en", "English", "English", True, True),
            ],
        )

    conn.commit()


def _list_languages_from_db(enabled_only: bool) -> list[dict[str, str | bool]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url()) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            if enabled_only:
                cur.execute(
                    """
                    SELECT code, name, native_name, enabled, system
                    FROM app_languages
                    WHERE enabled = TRUE
                    ORDER BY code
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT code, name, native_name, enabled, system
                    FROM app_languages
                    ORDER BY code
                    """
                )

            rows = cur.fetchall()

    return [
        {
            "code": row[0],
            "name": row[1],
            "native_name": row[2],
            "enabled": row[3],
            "system": row[4],
        }
        for row in rows
    ]


def _add_language_to_db(code: str, name: str, native_name: str) -> dict[str, str | bool]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url()) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM app_languages WHERE code = %s", (code,))
            if cur.fetchone() is not None:
                raise ValueError("language already exists")

            cur.execute(
                """
                INSERT INTO app_languages(code, name, native_name, enabled, system)
                VALUES (%s, %s, %s, TRUE, FALSE)
                """,
                (code, name, native_name),
            )

        conn.commit()

    return {
        "code": code,
        "name": name,
        "native_name": native_name,
        "enabled": True,
        "system": False,
    }


def _set_language_enabled_db(code: str, enabled: bool) -> dict[str, str | bool]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url()) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code, name, native_name, enabled, system FROM app_languages WHERE code = %s",
                (code,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("language not found")

            if row[4] and not enabled:
                raise ValueError("system language cannot be disabled")

            cur.execute("UPDATE app_languages SET enabled = %s WHERE code = %s", (enabled, code))
            cur.execute(
                "SELECT code, name, native_name, enabled, system FROM app_languages WHERE code = %s",
                (code,),
            )
            updated = cur.fetchone()

        conn.commit()

    return {
        "code": updated[0],
        "name": updated[1],
        "native_name": updated[2],
        "enabled": updated[3],
        "system": updated[4],
    }


def _delete_language_db(code: str) -> None:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url()) as conn:
        _ensure_schema_and_seed(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT system FROM app_languages WHERE code = %s", (code,))
            row = cur.fetchone()
            if row is None:
                raise ValueError("language not found")
            if row[0]:
                raise ValueError("system language cannot be deleted")

            cur.execute("DELETE FROM app_languages WHERE code = %s", (code,))

        conn.commit()


def normalize_code(code: str) -> str:
    normalized = code.strip().lower()
    if not LANGUAGE_CODE_PATTERN.match(normalized):
        raise ValueError("invalid language code format")
    return normalized


def list_languages(enabled_only: bool = False) -> list[dict[str, str | bool]]:
    if _use_database():
        return _list_languages_from_db(enabled_only)

    items = [entry for entry in languages.values() if (entry.enabled or not enabled_only)]
    items.sort(key=lambda item: item.code)
    return [
        {
            "code": item.code,
            "name": item.name,
            "native_name": item.native_name,
            "enabled": item.enabled,
            "system": item.system,
        }
        for item in items
    ]


def list_language_catalog() -> list[dict[str, str]]:
    return sorted(LANGUAGE_CATALOG, key=lambda item: (item["name"], item["code"]))


def add_language(code: str, name: str, native_name: str | None = None) -> dict[str, str | bool]:
    normalized_code = normalize_code(code)
    language_name = name.strip()
    local_name = (native_name or name).strip()

    if not language_name:
        raise ValueError("language name is required")

    if _use_database():
        return _add_language_to_db(normalized_code, language_name, local_name)

    if normalized_code in languages:
        raise ValueError("language already exists")

    entry = LanguageEntry(
        code=normalized_code,
        name=language_name,
        native_name=local_name,
        enabled=True,
        system=False,
    )
    languages[normalized_code] = entry

    return {
        "code": entry.code,
        "name": entry.name,
        "native_name": entry.native_name,
        "enabled": entry.enabled,
        "system": entry.system,
    }


def set_language_enabled(code: str, enabled: bool) -> dict[str, str | bool]:
    normalized_code = normalize_code(code)

    if _use_database():
        return _set_language_enabled_db(normalized_code, enabled)

    entry = languages.get(normalized_code)
    if entry is None:
        raise ValueError("language not found")
    if entry.system and not enabled:
        raise ValueError("system language cannot be disabled")

    entry.enabled = enabled
    return {
        "code": entry.code,
        "name": entry.name,
        "native_name": entry.native_name,
        "enabled": entry.enabled,
        "system": entry.system,
    }


def delete_language(code: str) -> None:
    normalized_code = normalize_code(code)

    if _use_database():
        _delete_language_db(normalized_code)
        return

    entry = languages.get(normalized_code)
    if entry is None:
        raise ValueError("language not found")
    if entry.system:
        raise ValueError("system language cannot be deleted")

    del languages[normalized_code]
