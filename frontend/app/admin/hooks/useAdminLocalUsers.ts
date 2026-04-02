import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, InlineFeedback, LocalUser, SupportedLanguage, TxFn } from "../types";

const LOCAL_USERS_BFF_BASE = "/api/bff/admin/local-users";

function localUsersBffPath(path = ""): string {
  return `${LOCAL_USERS_BFF_BASE}${path}`;
}

function extractErrorDetail(errorBody: unknown, fallbackStatus: number): string {
  if (errorBody && typeof errorBody === "object") {
    const body = errorBody as { detail?: unknown; error?: { detail?: unknown } };
    if (typeof body.detail === "string" && body.detail.trim().length > 0) {
      return body.detail;
    }
    if (typeof body.error?.detail === "string" && body.error.detail.trim().length > 0) {
      return body.error.detail;
    }
  }
  return String(fallbackStatus);
}

type LoadLocalUsersOverrides = {
  search?: string;
  role?: string;
  language?: string;
};

type UseAdminLocalUsersParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  supportedLanguages: SupportedLanguage[];
  tx: TxFn;
  onAfterCreate?: () => Promise<void> | void;
  onAfterMutate?: () => Promise<void> | void;
};

type UseAdminLocalUsersResult = {
  localUsers: LocalUser[];
  localFeedback: InlineFeedback | null;
  localCreateBusy: boolean;
  localListBusy: boolean;
  localDeleteBusy: boolean;
  localUpdateBusy: boolean;
  localPasswordBusy: boolean;
  localLogin: string;
  localPassword: string;
  localDisplayName: string;
  localRoles: string;
  localDefaultLanguage: string;
  localSearch: string;
  localRoleFilter: string;
  localLanguageFilter: string;
  selectedLocalUser: LocalUser | null;
  selectedLocalUserId: string;
  editLocalDisplayName: string;
  editLocalLanguage: string;
  editLocalRoles: string;
  editLocalPassword: string;
  editLocalPasswordConfirm: string;
  localFilterBadges: string[];
  localUpdateHasChanges: boolean;
  setLocalLogin: (value: string) => void;
  setLocalPassword: (value: string) => void;
  setLocalDisplayName: (value: string) => void;
  setLocalRoles: (value: string) => void;
  setLocalDefaultLanguage: (value: string) => void;
  setLocalSearch: (value: string) => void;
  setLocalRoleFilter: (value: string) => void;
  setLocalLanguageFilter: (value: string) => void;
  setEditLocalDisplayName: (value: string) => void;
  setEditLocalLanguage: (value: string) => void;
  setEditLocalRoles: (value: string) => void;
  setEditLocalPassword: (value: string) => void;
  setEditLocalPasswordConfirm: (value: string) => void;
  loadLocalUsers: (overrides?: LoadLocalUsersOverrides) => Promise<void>;
  createLocalUser: () => Promise<void>;
  selectLocalUser: (userId: string) => void;
  revertLocalUserForm: () => void;
  clearLocalFilters: () => Promise<void>;
  updateLocalUser: () => Promise<void>;
  updateLocalUserPassword: () => Promise<void>;
  deleteLocalUser: () => Promise<void>;
};

export function useAdminLocalUsers({
  activeTab,
  buildAuthHeaders,
  l,
  supportedLanguages,
  tx,
  onAfterCreate,
  onAfterMutate,
}: UseAdminLocalUsersParams): UseAdminLocalUsersResult {
  const [localUsers, setLocalUsers] = useState<LocalUser[]>([]);
  const [localFeedback, setLocalFeedback] = useState<InlineFeedback | null>(null);
  const [localCreateBusy, setLocalCreateBusy] = useState(false);
  const [localListBusy, setLocalListBusy] = useState(false);
  const [localDeleteBusy, setLocalDeleteBusy] = useState(false);
  const [localUpdateBusy, setLocalUpdateBusy] = useState(false);
  const [localPasswordBusy, setLocalPasswordBusy] = useState(false);
  const [localLogin, setLocalLogin] = useState("");
  const [localPassword, setLocalPassword] = useState("");
  const [localDisplayName, setLocalDisplayName] = useState("");
  const [localRoles, setLocalRoles] = useState("student");
  const [localDefaultLanguage, setLocalDefaultLanguage] = useState("ru");
  const [localSearch, setLocalSearch] = useState("");
  const [localRoleFilter, setLocalRoleFilter] = useState("");
  const [localLanguageFilter, setLocalLanguageFilter] = useState("");
  const [selectedLocalUserId, setSelectedLocalUserId] = useState("");
  const [editLocalDisplayName, setEditLocalDisplayName] = useState("");
  const [editLocalLanguage, setEditLocalLanguage] = useState("ru");
  const [editLocalRoles, setEditLocalRoles] = useState("student");
  const [editLocalPassword, setEditLocalPassword] = useState("");
  const [editLocalPasswordConfirm, setEditLocalPasswordConfirm] = useState("");

  const selectedLocalUser = useMemo(
    () => localUsers.find((item) => item.user_id === selectedLocalUserId) || null,
    [localUsers, selectedLocalUserId],
  );

  const localFilterBadges = useMemo(
    () => [
      localSearch.trim() ? `${tx("localFilterSearch")}: ${localSearch.trim()}` : "",
      localRoleFilter.trim() ? `${tx("localFilterRole")}: ${localRoleFilter.trim()}` : "",
      localLanguageFilter.trim() ? `${tx("localFilterLanguage")}: ${localLanguageFilter.trim()}` : "",
    ].filter(Boolean),
    [localLanguageFilter, localRoleFilter, localSearch, tx],
  );

  const localUpdateHasChanges = useMemo(() => {
    if (!selectedLocalUser) {
      return false;
    }

    const displayChanged = selectedLocalUser.display_name.trim() !== editLocalDisplayName.trim();
    const languageChanged = selectedLocalUser.default_language.trim().toLowerCase() !== editLocalLanguage.trim().toLowerCase();

    const originalRoles = [...selectedLocalUser.roles].map((item) => item.trim()).filter(Boolean).sort();
    const editedRoles = editLocalRoles
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .sort();
    const rolesChanged = JSON.stringify(originalRoles) !== JSON.stringify(editedRoles);

    return displayChanged || languageChanged || rolesChanged;
  }, [editLocalDisplayName, editLocalLanguage, editLocalRoles, selectedLocalUser]);

  const loadLocalUsers = useCallback(async (overrides?: LoadLocalUsersOverrides) => {
    setLocalListBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const effectiveSearch = overrides?.search ?? localSearch;
      const effectiveRole = overrides?.role ?? localRoleFilter;
      const effectiveLanguage = overrides?.language ?? localLanguageFilter;
      const params = new URLSearchParams();
      if (effectiveSearch.trim()) {
        params.set("search", effectiveSearch.trim());
      }
      if (effectiveRole.trim()) {
        params.set("role", effectiveRole.trim());
      }
      if (effectiveLanguage.trim()) {
        params.set("language", effectiveLanguage.trim());
      }

      const query = params.toString();
      const endpoint = query ? `${localUsersBffPath()}?${query}` : localUsersBffPath();
      const res = await fetch(endpoint, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      const json = (await res.json()) as { users?: LocalUser[] };
      setLocalUsers(json.users || []);
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalListBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, localLanguageFilter, localRoleFilter, localSearch]);

  const createLocalUser = useCallback(async () => {
    setLocalFeedback(null);
    if (!localLogin.trim() || !localPassword.trim() || !localDisplayName.trim()) {
      setLocalFeedback({ tone: "error", message: l.localUserRequired });
      return;
    }

    setLocalCreateBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(localUsersBffPath(), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          login: localLogin,
          password: localPassword,
          display_name: localDisplayName,
          roles: localRoles
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          default_language: localDefaultLanguage,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      setLocalLogin("");
      setLocalPassword("");
      setLocalDisplayName("");
      setLocalRoles("student");
      setLocalDefaultLanguage("ru");
      await loadLocalUsers();
      await onAfterCreate?.();
      setLocalFeedback({ tone: "success", message: l.localUserCreated });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalCreateBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, l.localUserCreated, l.localUserRequired, loadLocalUsers, localDefaultLanguage, localDisplayName, localLogin, localPassword, localRoles, onAfterCreate]);

  const selectLocalUser = useCallback((userId: string) => {
    const selected = localUsers.find((item) => item.user_id === userId);
    if (!selected) {
      return;
    }
    setSelectedLocalUserId(selected.user_id);
    setEditLocalDisplayName(selected.display_name);
    setEditLocalLanguage(selected.default_language);
    setEditLocalRoles(selected.roles.join(","));
    setEditLocalPassword("");
    setEditLocalPasswordConfirm("");
  }, [localUsers]);

  const revertLocalUserForm = useCallback(() => {
    if (!selectedLocalUser) {
      return;
    }

    setEditLocalDisplayName(selectedLocalUser.display_name);
    setEditLocalLanguage(selectedLocalUser.default_language);
    setEditLocalRoles(selectedLocalUser.roles.join(","));
    setEditLocalPassword("");
    setEditLocalPasswordConfirm("");
    setLocalFeedback({ tone: "info", message: tx("localFormReverted") });
  }, [selectedLocalUser, tx]);

  const clearLocalFilters = useCallback(async () => {
    setLocalSearch("");
    setLocalRoleFilter("");
    setLocalLanguageFilter("");
    setLocalFeedback(null);
    await loadLocalUsers({ search: "", role: "", language: "" });
  }, [loadLocalUsers]);

  const updateLocalUser = useCallback(async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired") });
      return;
    }
    if (!localUpdateHasChanges) {
      setLocalFeedback({ tone: "info", message: tx("localNoChanges") });
      return;
    }

    setLocalUpdateBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(localUsersBffPath(`/${encodeURIComponent(selectedLocalUserId)}`), {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          display_name: editLocalDisplayName,
          language: editLocalLanguage,
          roles: editLocalRoles
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      await loadLocalUsers();
      await onAfterMutate?.();
      setLocalFeedback({ tone: "success", message: tx("localUserUpdated") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalUpdateBusy(false);
    }
  }, [buildAuthHeaders, editLocalDisplayName, editLocalLanguage, editLocalRoles, l.errorPrefix, loadLocalUsers, localUpdateHasChanges, onAfterMutate, selectedLocalUserId, tx]);

  const updateLocalUserPassword = useCallback(async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired") });
      return;
    }
    if (!editLocalPassword.trim()) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordRequired") });
      return;
    }
    if (editLocalPassword.trim().length < 6) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordMinLength") });
      return;
    }
    if (editLocalPassword !== editLocalPasswordConfirm) {
      setLocalFeedback({ tone: "error", message: tx("localPasswordMismatch") });
      return;
    }

    setLocalPasswordBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(localUsersBffPath(`/${encodeURIComponent(selectedLocalUserId)}/password`), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({ password: editLocalPassword }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      setEditLocalPassword("");
      setEditLocalPasswordConfirm("");
      setLocalFeedback({ tone: "success", message: tx("localPasswordUpdated") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalPasswordBusy(false);
    }
  }, [buildAuthHeaders, editLocalPassword, editLocalPasswordConfirm, l.errorPrefix, selectedLocalUserId, tx]);

  const deleteLocalUser = useCallback(async () => {
    setLocalFeedback(null);
    if (!selectedLocalUserId) {
      setLocalFeedback({ tone: "error", message: tx("localUserSelectRequired") });
      return;
    }

    const target = localUsers.find((item) => item.user_id === selectedLocalUserId);
    const confirmed = window.confirm(
      tx("localDeleteConfirm") +
      (target ? `\n${target.display_name} (${target.login}) [${target.user_id}]` : ""),
    );
    if (!confirmed) {
      setLocalFeedback({ tone: "info", message: tx("localDeleteCancelled") });
      return;
    }

    setLocalDeleteBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(localUsersBffPath(`/${encodeURIComponent(selectedLocalUserId)}`), {
        method: "DELETE",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLocalFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
        });
        return;
      }

      await loadLocalUsers();
      await onAfterMutate?.();
      setLocalFeedback({ tone: "success", message: tx("localUserDeleted") });
    } catch (error) {
      setLocalFeedback({ tone: "error", message: String(error) });
    } finally {
      setLocalDeleteBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, loadLocalUsers, localUsers, onAfterMutate, selectedLocalUserId, tx]);

  useEffect(() => {
    if (activeTab !== "local-users") {
      return;
    }
    void loadLocalUsers();
  }, [activeTab, loadLocalUsers]);

  useEffect(() => {
    if (localUsers.length === 0) {
      setSelectedLocalUserId("");
      setEditLocalDisplayName("");
      setEditLocalLanguage("ru");
      setEditLocalRoles("student");
      return;
    }

    const selected = localUsers.find((item) => item.user_id === selectedLocalUserId) || localUsers[0];
    setSelectedLocalUserId(selected.user_id);
    setEditLocalDisplayName(selected.display_name);
    setEditLocalLanguage(selected.default_language);
    setEditLocalRoles(selected.roles.join(","));
  }, [localUsers, selectedLocalUserId]);

  useEffect(() => {
    setLocalDefaultLanguage((current) => current || supportedLanguages.find((item) => item.enabled)?.code || "ru");
  }, [supportedLanguages]);

  return {
    localUsers,
    localFeedback,
    localCreateBusy,
    localListBusy,
    localDeleteBusy,
    localUpdateBusy,
    localPasswordBusy,
    localLogin,
    localPassword,
    localDisplayName,
    localRoles,
    localDefaultLanguage,
    localSearch,
    localRoleFilter,
    localLanguageFilter,
    selectedLocalUser,
    selectedLocalUserId,
    editLocalDisplayName,
    editLocalLanguage,
    editLocalRoles,
    editLocalPassword,
    editLocalPasswordConfirm,
    localFilterBadges,
    localUpdateHasChanges,
    setLocalLogin,
    setLocalPassword,
    setLocalDisplayName,
    setLocalRoles,
    setLocalDefaultLanguage,
    setLocalSearch,
    setLocalRoleFilter,
    setLocalLanguageFilter,
    setEditLocalDisplayName,
    setEditLocalLanguage,
    setEditLocalRoles,
    setEditLocalPassword,
    setEditLocalPasswordConfirm,
    loadLocalUsers,
    createLocalUser,
    selectLocalUser,
    revertLocalUserForm,
    clearLocalFilters,
    updateLocalUser,
    updateLocalUserPassword,
    deleteLocalUser,
  };
}
