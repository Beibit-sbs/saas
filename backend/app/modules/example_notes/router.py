from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.modules.audit.service import log_admin_action
from app.modules.example_notes.service import (
    create_example_note,
    delete_example_note,
    list_example_notes,
    update_example_note,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/example-notes", tags=["example-notes"])


class ExampleNoteCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=2000)
    is_active: bool = True


class ExampleNoteUpdatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=2000)
    is_active: bool = True


@router.get("")
def get_example_notes(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("example.notes.read"))],
) -> dict[str, list[dict[str, object]]]:
    return {"notes": list_example_notes()}


@router.post("")
def create_example_note_endpoint(
    payload: ExampleNoteCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("example.notes.manage"))],
) -> dict[str, dict[str, object]]:
    try:
        note = create_example_note(payload.title, payload.summary, payload.is_active)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        action="example_notes.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="example_notes",
        result="success",
        metadata={
            "note_id": note["id"],
            "title": note["title"],
            "is_active": note["is_active"],
        },
    )
    return {"note": note}


@router.put("/{note_id}")
def update_example_note_endpoint(
    note_id: int,
    payload: ExampleNoteUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("example.notes.manage"))],
) -> dict[str, dict[str, object]]:
    try:
        note = update_example_note(note_id, payload.title, payload.summary, payload.is_active)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="example_notes.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="example_notes",
        result="success",
        metadata={
            "note_id": note["id"],
            "title": note["title"],
            "is_active": note["is_active"],
        },
    )
    return {"note": note}


@router.delete("/{note_id}")
def delete_example_note_endpoint(
    note_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("example.notes.manage"))],
) -> dict[str, object]:
    try:
        note = delete_example_note(note_id)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        action="example_notes.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="example_notes",
        result="success",
        metadata={
            "note_id": note["id"],
            "title": note["title"],
            "is_active": note["is_active"],
        },
    )
    return {"deleted": True, "note": note}
