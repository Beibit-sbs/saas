"use client";

import type { AdminTranslationKey } from "../../../i18n/admin";
import { useAdminExampleNotes } from "../hooks/useAdminExampleNotes";

type AdminExampleNotesTabProps = {
  buildAuthHeaders: () => Record<string, string>;
  tx: (key: AdminTranslationKey, fallback?: string) => string;
};

export function AdminExampleNotesTab({ buildAuthHeaders, tx }: AdminExampleNotesTabProps) {
  const {
    notes,
    title,
    summary,
    isActive,
    editingId,
    loading,
    saving,
    deletingId,
    feedback,
    setTitle,
    setSummary,
    setIsActive,
    resetForm,
    handleSubmit,
    handleEdit,
    handleDelete,
  } = useAdminExampleNotes({ buildAuthHeaders, tx });

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
