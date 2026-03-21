from pathlib import Path

from tests.conftest import ADMIN_HEADERS, _auth_headers, client
from app.modules.audit.service import list_admin_actions
from app.modules.example_notes import service as example_notes_service


def test_example_notes_crud_flow() -> None:
    list_response = client.get("/api/admin/example-notes", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert list_response.json()["notes"] == []

    create_response = client.post(
        "/api/admin/example-notes",
        json={"title": "Example note", "summary": "Reference summary", "is_active": True},
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    created = create_response.json()["note"]
    assert created["title"] == "Example note"
    assert created["summary"] == "Reference summary"
    assert created["is_active"] is True

    list_after_create = client.get("/api/admin/example-notes", headers=ADMIN_HEADERS)
    assert list_after_create.status_code == 200
    assert len(list_after_create.json()["notes"]) == 1

    update_response = client.put(
        f"/api/admin/example-notes/{created['id']}",
        json={"title": "Updated example note", "summary": "Updated summary", "is_active": False},
        headers=ADMIN_HEADERS,
    )
    assert update_response.status_code == 200
    updated = update_response.json()["note"]
    assert updated["title"] == "Updated example note"
    assert updated["summary"] == "Updated summary"
    assert updated["is_active"] is False

    delete_response = client.delete(
        f"/api/admin/example-notes/{created['id']}",
        headers=ADMIN_HEADERS,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    list_after_delete = client.get("/api/admin/example-notes", headers=ADMIN_HEADERS)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["notes"] == []


def test_example_notes_permission_protection() -> None:
    student_headers = _auth_headers("student.example", ["student"])
    auditor_headers = _auth_headers("auditor.example", ["auditor"])

    read_denied = client.get("/api/admin/example-notes", headers=student_headers)
    assert read_denied.status_code == 403

    read_allowed = client.get("/api/admin/example-notes", headers=auditor_headers)
    assert read_allowed.status_code == 200

    manage_denied = client.post(
        "/api/admin/example-notes",
        json={"title": "Blocked", "summary": "Blocked", "is_active": True},
        headers=auditor_headers,
    )
    assert manage_denied.status_code == 403


def test_example_notes_mutations_are_audited() -> None:
    create_response = client.post(
        "/api/admin/example-notes",
        json={"title": "Audit note", "summary": "Create me", "is_active": True},
        headers=ADMIN_HEADERS,
    )
    assert create_response.status_code == 200
    note_id = create_response.json()["note"]["id"]

    update_response = client.put(
        f"/api/admin/example-notes/{note_id}",
        json={"title": "Audit note updated", "summary": "Updated", "is_active": True},
        headers=ADMIN_HEADERS,
    )
    assert update_response.status_code == 200

    delete_response = client.delete(f"/api/admin/example-notes/{note_id}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 200

    create_events = list_admin_actions(action="example_notes.create", entity="example_notes", limit=20, tenant_id=1)
    update_events = list_admin_actions(action="example_notes.update", entity="example_notes", limit=20, tenant_id=1)
    delete_events = list_admin_actions(action="example_notes.delete", entity="example_notes", limit=20, tenant_id=1)

    assert any(event.get("path") == "/api/admin/example-notes" for event in create_events)
    assert any(event.get("path") == f"/api/admin/example-notes/{note_id}" for event in update_events)
    assert any(event.get("path") == f"/api/admin/example-notes/{note_id}" for event in delete_events)


def test_example_notes_service_dispatches_to_database_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(example_notes_service, "_use_database", lambda: True)
    monkeypatch.setattr(
        example_notes_service,
        "_list_example_notes_db",
        lambda: [
            {
                "id": 7,
                "title": "DB note",
                "summary": "From DB",
                "is_active": True,
                "created_at": "2026-03-18T00:00:00+00:00",
                "updated_at": "2026-03-18T00:00:00+00:00",
            }
        ],
    )

    notes = example_notes_service.list_example_notes()
    assert len(notes) == 1
    assert notes[0]["id"] == 7
    assert notes[0]["title"] == "DB note"


def test_example_notes_migration_exists_and_seeds_permissions() -> None:
    migration_path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "e4c4a8df6d21_add_example_notes_table.py"
    assert migration_path.exists()

    migration_text = migration_path.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS example_notes" in migration_text
    assert "example.notes.read" in migration_text
    assert "example.notes.manage" in migration_text
