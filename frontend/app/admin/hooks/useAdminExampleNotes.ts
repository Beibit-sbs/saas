import { useCallback, useEffect, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { InlineFeedback, TxFn } from "../types";

export type ExampleNote = {
  id: number;
  title: string;
  summary: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type UseAdminExampleNotesParams = {
  buildAuthHeaders: () => Record<string, string>;
  tx: TxFn;
};

type UseAdminExampleNotesResult = {
  notes: ExampleNote[];
  title: string;
  summary: string;
  isActive: boolean;
  editingId: number | null;
  loading: boolean;
  saving: boolean;
  deletingId: number | null;
  feedback: InlineFeedback | null;
  setTitle: (value: string) => void;
  setSummary: (value: string) => void;
  setIsActive: (value: boolean) => void;
  resetForm: () => void;
  handleSubmit: () => Promise<void>;
  handleEdit: (note: ExampleNote) => void;
  handleDelete: (note: ExampleNote) => Promise<void>;
};

export function useAdminExampleNotes({
  buildAuthHeaders,
  tx,
}: UseAdminExampleNotesParams): UseAdminExampleNotesResult {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

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
      const endpoint =
        editingId === null
          ? `${baseUrl}/admin/example-notes`
          : `${baseUrl}/admin/example-notes/${editingId}`;
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
        message:
          editingId === null
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

  const handleEdit = useCallback(
    (note: ExampleNote) => {
      setEditingId(note.id);
      setTitle(note.title);
      setSummary(note.summary);
      setIsActive(note.is_active);
      setFeedback({ tone: "info", message: tx("exampleNotesEditing", "Editing example note.") });
    },
    [tx],
  );

  const handleDelete = useCallback(
    async (note: ExampleNote) => {
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
    },
    [baseUrl, buildAuthHeaders, editingId, loadNotes, resetForm, tx],
  );

  return {
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
  };
}
