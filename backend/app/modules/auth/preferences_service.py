import os

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


in_memory_preferences: dict[str, str] = {}


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _ensure_preferences_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_user_preferences (
                user_id TEXT PRIMARY KEY,
                language_code TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    conn.commit()


def get_user_language(user_id: str) -> str | None:
    if _use_database():
        with psycopg.connect(_db_url()) as conn:
            _ensure_preferences_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT language_code FROM app_user_preferences WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                return row[0] if row else None

    return in_memory_preferences.get(user_id)


def set_user_language(user_id: str, language_code: str) -> str:
    if _use_database():
        with psycopg.connect(_db_url()) as conn:
            _ensure_preferences_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO app_user_preferences(user_id, language_code, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id)
                    DO UPDATE SET language_code = EXCLUDED.language_code, updated_at = NOW()
                    """,
                    (user_id, language_code),
                )
            conn.commit()
        return language_code

    in_memory_preferences[user_id] = language_code
    return language_code
