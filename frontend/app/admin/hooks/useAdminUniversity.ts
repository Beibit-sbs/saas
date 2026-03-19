import { useCallback, useEffect, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminTab, InlineFeedback } from "../types";

export type UniversityEntity = "students" | "faculty" | "programs" | "courses" | "enrollments" | "records";

const ENTITY_ENDPOINT: Record<UniversityEntity, string> = {
  students: "students",
  faculty: "faculty",
  programs: "programs",
  courses: "courses",
  enrollments: "enrollments",
  records: "records",
};

const ENTITY_LIST_KEY: Record<UniversityEntity, string> = {
  students: "students",
  faculty: "faculty",
  programs: "programs",
  courses: "courses",
  enrollments: "enrollments",
  records: "records",
};

const ENTITY_ITEM_KEY: Record<UniversityEntity, string> = {
  students: "student",
  faculty: "faculty",
  programs: "program",
  courses: "course",
  enrollments: "enrollment",
  records: "record",
};

type UseAdminUniversityParams = {
  activeTab: AdminTab;
  buildAuthHeaders: () => Record<string, string>;
};

type UseAdminUniversityResult = {
  activeEntity: UniversityEntity;
  setActiveEntity: (value: UniversityEntity) => void;
  itemsByEntity: Record<UniversityEntity, Array<Record<string, unknown>>>;
  loading: boolean;
  mutating: boolean;
  feedback: InlineFeedback | null;
  lastUpdated: string;
  refresh: (entity?: UniversityEntity) => Promise<void>;
  createItem: (entity: UniversityEntity, payload: Record<string, unknown>) => Promise<Record<string, unknown> | null>;
  updateItem: (entity: UniversityEntity, id: number, payload: Record<string, unknown>) => Promise<Record<string, unknown> | null>;
  deleteItem: (entity: UniversityEntity, id: number) => Promise<boolean>;
};

const EMPTY_ENTITY_DATA: Record<UniversityEntity, Array<Record<string, unknown>>> = {
  students: [],
  faculty: [],
  programs: [],
  courses: [],
  enrollments: [],
  records: [],
};

export function useAdminUniversity({
  activeTab,
  buildAuthHeaders,
}: UseAdminUniversityParams): UseAdminUniversityResult {
  const [activeEntity, setActiveEntity] = useState<UniversityEntity>("students");
  const [itemsByEntity, setItemsByEntity] = useState<Record<UniversityEntity, Array<Record<string, unknown>>>>(EMPTY_ENTITY_DATA);
  const [loading, setLoading] = useState(false);
  const [mutating, setMutating] = useState(false);
  const [feedback, setFeedback] = useState<InlineFeedback | null>(null);
  const [lastUpdated, setLastUpdated] = useState("-");

  const refresh = useCallback(
    async (entity: UniversityEntity = activeEntity) => {
      setLoading(true);
      if (!mutating) {
        setFeedback(null);
      }
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const endpoint = ENTITY_ENDPOINT[entity];
        const listKey = ENTITY_LIST_KEY[entity];
        const res = await fetch(`${baseUrl}/admin/university/${endpoint}`, {
          headers: buildAuthHeaders(),
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({
            tone: "error",
            message: `Error: ${String(err.detail || res.status)}`,
          });
          return;
        }

        const json = (await res.json()) as Record<string, Array<Record<string, unknown>> | undefined>;
        const rows = json[listKey] || [];
        setItemsByEntity((current) => ({ ...current, [entity]: rows }));
        setLastUpdated(new Date().toLocaleString());
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
      } finally {
        setLoading(false);
      }
    },
    [activeEntity, buildAuthHeaders, mutating],
  );

  const createItem = useCallback(
    async (entity: UniversityEntity, payload: Record<string, unknown>) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const endpoint = ENTITY_ENDPOINT[entity];
        const itemKey = ENTITY_ITEM_KEY[entity];
        const res = await fetch(`${baseUrl}/admin/university/${endpoint}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...buildAuthHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String(err.detail || res.status)}` });
          return null;
        }

        const json = (await res.json()) as Record<string, Record<string, unknown> | undefined>;
        setFeedback({ tone: "success", message: "Created successfully" });
        await refresh(entity);
        return json[itemKey] || null;
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
        return null;
      } finally {
        setMutating(false);
      }
    },
    [buildAuthHeaders, refresh],
  );

  const updateItem = useCallback(
    async (entity: UniversityEntity, id: number, payload: Record<string, unknown>) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const endpoint = ENTITY_ENDPOINT[entity];
        const itemKey = ENTITY_ITEM_KEY[entity];
        const res = await fetch(`${baseUrl}/admin/university/${endpoint}/${id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...buildAuthHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String(err.detail || res.status)}` });
          return null;
        }

        const json = (await res.json()) as Record<string, Record<string, unknown> | undefined>;
        setFeedback({ tone: "success", message: "Updated successfully" });
        await refresh(entity);
        return json[itemKey] || null;
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
        return null;
      } finally {
        setMutating(false);
      }
    },
    [buildAuthHeaders, refresh],
  );

  const deleteItem = useCallback(
    async (entity: UniversityEntity, id: number) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const endpoint = ENTITY_ENDPOINT[entity];
        const res = await fetch(`${baseUrl}/admin/university/${endpoint}/${id}`, {
          method: "DELETE",
          headers: {
            ...buildAuthHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String(err.detail || res.status)}` });
          return false;
        }

        setFeedback({ tone: "success", message: "Deleted successfully" });
        await refresh(entity);
        return true;
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
        return false;
      } finally {
        setMutating(false);
      }
    },
    [buildAuthHeaders, refresh],
  );

  useEffect(() => {
    if (activeTab !== "university") {
      return;
    }
    void refresh(activeEntity);
  }, [activeTab, activeEntity, refresh]);

  return {
    activeEntity,
    setActiveEntity,
    itemsByEntity,
    loading,
    mutating,
    feedback,
    lastUpdated,
    refresh,
    createItem,
    updateItem,
    deleteItem,
  };
}
