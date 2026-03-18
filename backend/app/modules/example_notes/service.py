from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from threading import Lock
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


@dataclass
class ExampleNoteEntry:
    id: int
    title: str
    summary: str
    is_active: bool
    created_at: str
    updated_at: str


_notes_lock = Lock()
_notes: dict[int, ExampleNoteEntry] = {}
_note_counter = 0


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError, ValueError)):
        return True
    if psycopg is not None and isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_title(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("title is required")
    if len(normalized) > 200:
        raise ValueError("title must be at most 200 characters")
    return normalized


def _normalize_summary(value: str) -> str:
    normalized = value.strip()
    if len(normalized) > 2000:
        raise ValueError("summary must be at most 2000 characters")
    return normalized


def _row_to_note(row: tuple[Any, ...]) -> dict[str, object]:
    created_at = row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4])
    updated_at = row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5])
    return {
        "id": row[0],
        "title": row[1],
        "summary": row[2],
        "is_active": bool(row[3]),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def _list_example_notes_db() -> list[dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, summary, is_active, created_at, updated_at
                FROM example_notes
                ORDER BY id ASC
                """
            )
            return [_row_to_note(row) for row in cur.fetchall()]


def _create_example_note_db(title: str, summary: str, is_active: bool) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO example_notes (title, summary, is_active)
                VALUES (%s, %s, %s)
                RETURNING id, title, summary, is_active, created_at, updated_at
                """,
                (title, summary, is_active),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise RuntimeError("failed to create example note")
    return _row_to_note(row)


def _update_example_note_db(note_id: int, title: str, summary: str, is_active: bool) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE example_notes
                SET title = %s,
                    summary = %s,
                    is_active = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, title, summary, is_active, created_at, updated_at
                """,
                (title, summary, is_active, note_id),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError("example note not found")
    return _row_to_note(row)


def _delete_example_note_db(note_id: int) -> dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with psycopg.connect(_db_url(), connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM example_notes
                WHERE id = %s
                RETURNING id, title, summary, is_active, created_at, updated_at
                """,
                (note_id,),
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        raise ValueError("example note not found")
    return _row_to_note(row)


def clear_example_notes() -> None:
    global _note_counter
    with _notes_lock:
        _notes.clear()
        _note_counter = 0


def list_example_notes() -> list[dict[str, object]]:
    if _use_database():
        try:
            return _list_example_notes_db()
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _notes_lock:
        return [
            {
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in sorted(_notes.values(), key=lambda current: current.id)
        ]


def create_example_note(title: str, summary: str, is_active: bool = True) -> dict[str, object]:
    normalized_title = _normalize_title(title)
    normalized_summary = _normalize_summary(summary)

    if _use_database():
        try:
            return _create_example_note_db(normalized_title, normalized_summary, is_active)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    global _note_counter
    now = _now_iso()
    with _notes_lock:
        _note_counter += 1
        entry = ExampleNoteEntry(
            id=_note_counter,
            title=normalized_title,
            summary=normalized_summary,
            is_active=bool(is_active),
            created_at=now,
            updated_at=now,
        )
        _notes[entry.id] = entry
        return {
            "id": entry.id,
            "title": entry.title,
            "summary": entry.summary,
            "is_active": entry.is_active,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }


def update_example_note(note_id: int, title: str, summary: str, is_active: bool) -> dict[str, object]:
    normalized_title = _normalize_title(title)
    normalized_summary = _normalize_summary(summary)

    if _use_database():
        try:
            return _update_example_note_db(note_id, normalized_title, normalized_summary, is_active)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _notes_lock:
        entry = _notes.get(note_id)
        if entry is None:
            raise ValueError("example note not found")
        entry.title = normalized_title
        entry.summary = normalized_summary
        entry.is_active = bool(is_active)
        entry.updated_at = _now_iso()
        return {
            "id": entry.id,
            "title": entry.title,
            "summary": entry.summary,
            "is_active": entry.is_active,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }


def delete_example_note(note_id: int) -> dict[str, object]:
    if _use_database():
        try:
            return _delete_example_note_db(note_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    with _notes_lock:
        entry = _notes.pop(note_id, None)
        if entry is None:
            raise ValueError("example note not found")
        return {
            "id": entry.id,
            "title": entry.title,
            "summary": entry.summary,
            "is_active": entry.is_active,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
