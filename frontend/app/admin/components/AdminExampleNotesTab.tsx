"use client";

import { useCallback, useEffect, useState } from "react";

import type { AdminTranslationKey } from "../../../i18n/admin";
import { buildCsrfHeaders } from "../../components/csrf";

type ExampleNote = {
  id: number;
  title: string;
  summary: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type InlineFeedback = {
  tone: "success" | "error" | "info";
  message: string;
};

type AdminExampleNotesTabProps = {
  baseUrl: string;
  buildAuthHeaders: () => Record<string, string>;
  tx: (key: AdminTranslationKey, fallback?: string) => string;
};

export function AdminExampleNotesTab({ baseUrl, buildAuthHeaders, tx }: AdminExampleNotesTabProps) {
  const [notes, setNotes] = useState<ExampleNote[]>([]);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<InlineFeedback | null>(null);

  const resetForm = useCallback(() => {
    setEditingId(null);
    setTitle("");
    setSummary("");
    setIsActive(true);
  }, []);

  const loadNotes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/example-notes`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({
          tone: "error",
          message: `${tx("errorPrefix", "Error")}: ${String(err.detail || res.status)}`,
        });
        return;
      }

      const json = (await res.json()) as { notes?: ExampleNote[] };
      setNotes(json.notes || []);
    } catch (error) {
      setFeedback({ tone: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  }, [baseUrl, buildAuthHeaders, tx]);

  useEffect(() => {
    void loadNotes();
  }, [loadNotes]);

  const handleSubmit = useCallback(async () => {
    if (!title.trim()) {
      setFeedback({ tone: "error", message: tx("exampleNotesTitleRequired", "Title is required.") });
      return;
    }

    setSaving(true);
    setFeedback(null);
    try {
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const endpoint = editingId === null ? `${baseUrl}/admin/example-notes` : `${baseUrl}/admin/example-notes/${editingId}`;
      const method = editingId === null ? "POST" : "PUT";
      const res = await fetch(endpoint, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({ title, summary, is_active: isActive }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({
          tone: "error",
          message: `${tx("errorPrefix", "Error")}: ${String(err.detail || res.status)}`,
        });
        return;
      }

      setFeedback({
        tone: "success",
        message: editingId === null
          ? tx("exampleNotesCreated", "Example note created.")
          : tx("exampleNotesUpdated", "Example note updated."),
      });
      resetForm();
      await loadNotes();
    } catch (error) {
      setFeedback({ tone: "error", message: String(error) });
    } finally {
      setSaving(false);
    }
  }, [baseUrl, buildAuthHeaders, editingId, isActive, loadNotes, resetForm, summary, title, tx]);

  const handleEdit = useCallback((note: ExampleNote) => {
    setEditingId(note.id);
    setTitle(note.title);
    setSummary(note.summary);
    setIsActive(note.is_active);
    setFeedback({ tone: "info", message: tx("exampleNotesEditing", "Editing example note.") });
  }, [tx]);

  const handleDelete = useCallback(async (note: ExampleNote) => {
    if (!window.confirm(tx("exampleNotesDeleteConfirm", "Delete this example note?"))) {
      return;
    }

    setDeletingId(note.id);
    setFeedback(null);
    try {
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/example-notes/${note.id}`, {
        method: "DELETE",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({
          tone: "error",
          message: `${tx("errorPrefix", "Error")}: ${String(err.detail || res.status)}`,
        });
        return;
      }

      if (editingId === note.id) {
        resetForm();
      }
      setFeedback({ tone: "success", message: tx("exampleNotesDeleted", "Example note deleted.") });
      await loadNotes();
    } catch (error) {
      setFeedback({ tone: "error", message: String(error) });
    } finally {
      setDeletingId(null);
    }
  }, [baseUrl, buildAuthHeaders, editingId, loadNotes, resetForm, tx]);

  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("exampleNotesTitle", "Example Notes")}</h2>
        <p className="subText">{tx("exampleNotesHelp", "Example-only CRUD module demonstrating DB-backed entity, RBAC, audit, migration, and i18n wiring.")}</p>
        <p className="subText"><b>{tx("exampleNotesReferenceLabel", "Reference only")}</b>: {tx("exampleNotesReferenceHelp", "Derived projects may remove or replace this module after copying the pattern.")}</p>
        {feedback ? (
          <p className={`inlineFeedback inlineFeedback${feedback.tone === "error" ? "Error" : feedback.tone === "success" ? "Success" : "Info"}`}>
            {feedback.message}
          </p>
        ) : null}
        <div className="formGrid" style={{ marginTop: 12 }}>
          <label>
            {tx("exampleNotesFieldTitle", "Title")}
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={tx("exampleNotesTitlePlaceholder", "Example note title")} />
          </label>
          <label>
            {tx("exampleNotesFieldSummary", "Summary")}
            <textarea value={summary} onChange={(e) => setSummary(e.target.value)} placeholder={tx("exampleNotesSummaryPlaceholder", "Short example summary")} rows={4} />
          </label>
          <label className="checkboxRow" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            <span>{tx("exampleNotesFieldIsActive", "Active")}</span>
          </label>
        </div>
        <div className="rowButtons">
          <button type="button" onClick={() => void handleSubmit()} disabled={saving}>
            {saving
              ? (editingId === null ? tx("saving", "Saving...") : tx("saving", "Saving..."))
              : (editingId === null ? tx("exampleNotesCreate", "Create example note") : tx("exampleNotesUpdate", "Update example note"))}
          </button>
          {editingId !== null ? (
            <button type="button" className="ghost" onClick={resetForm} disabled={saving}>
              {tx("exampleNotesCancelEdit", "Cancel edit")}
            </button>
          ) : null}
        </div>
      </article>

      <article className="panelCard">
        <h2>{tx("exampleNotesListTitle", "Stored example notes")}</h2>
        <p className="subText">{tx("exampleNotesListHelp", "Minimal admin-facing UI for list/create/edit/delete reference behavior.")}</p>
        {loading ? (
          <p className="subText">{tx("loading", "Loading...")}</p>
        ) : notes.length === 0 ? (
          <p className="subText">{tx("exampleNotesEmpty", "No example notes yet.")}</p>
        ) : (
          <ul className="plainList">
            {notes.map((note) => (
              <li key={note.id} style={{ marginBottom: 12 }}>
                <b>{note.title}</b>
                <div className="subText">{note.summary || tx("exampleNotesNoSummary", "No summary")}</div>
                <div className="subText">
                  {tx("exampleNotesFieldIsActive", "Active")}: {note.is_active ? tx("enabled", "Enabled") : tx("disabled", "Disabled")}
                  {` · ID ${note.id}`}
                </div>
                <div className="subText">{tx("lastChange", "Last change")}: {new Date(note.updated_at).toLocaleString()}</div>
                <div className="rowButtons">
                  <button type="button" className="ghost" onClick={() => handleEdit(note)}>{tx("exampleNotesEdit", "Edit")}</button>
                  <button type="button" className="ghost" onClick={() => void handleDelete(note)} disabled={deletingId === note.id}>
                    {deletingId === note.id ? tx("deleting", "Deleting...") : tx("delete", "Delete")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </article>
    </div>
  );
}
