import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, InlineFeedback, RbacAssignmentEntry, RbacRoleEntry, TxFn } from "../types";

type UseAdminRbacParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
  onAfterMutate?: () => Promise<void> | void;
};

type UseAdminRbacResult = {
  rbacFeedback: InlineFeedback | null;
  rbacRolesBusy: boolean;
  rbacRoleSaveBusy: boolean;
  rbacAssignmentsBusy: boolean;
  rbacAssignBusy: boolean;
  rbacRevokeBusyKey: string;
  rbacRoles: RbacRoleEntry[];
  rbacAssignments: RbacAssignmentEntry[];
  newRoleName: string;
  newRolePermissions: string;
  assignUserId: string;
  assignRoleName: string;
  assignmentUserFilter: string;
  assignmentRoleFilter: string;
  rbacFilterBadges: string[];
  rbacAssignmentRows: Array<{ user_id: string; role: string }>;
  setNewRoleName: (value: string) => void;
  setNewRolePermissions: (value: string) => void;
  setAssignUserId: (value: string) => void;
  setAssignRoleName: (value: string) => void;
  setAssignmentUserFilter: (value: string) => void;
  setAssignmentRoleFilter: (value: string) => void;
  loadRbacRoles: () => Promise<void>;
  loadRbacAssignments: () => Promise<void>;
  saveRbacRole: () => Promise<void>;
  assignRbacRole: () => Promise<void>;
  revokeRbacRole: (userId: string, role: string) => Promise<void>;
  clearRbacFilters: () => Promise<void>;
};

export function useAdminRbac({
  activeTab,
  buildAuthHeaders,
  l,
  tx,
  onAfterMutate,
}: UseAdminRbacParams): UseAdminRbacResult {
  const [rbacFeedback, setRbacFeedback] = useState<InlineFeedback | null>(null);
  const [rbacRolesBusy, setRbacRolesBusy] = useState(false);
  const [rbacRoleSaveBusy, setRbacRoleSaveBusy] = useState(false);
  const [rbacAssignmentsBusy, setRbacAssignmentsBusy] = useState(false);
  const [rbacAssignBusy, setRbacAssignBusy] = useState(false);
  const [rbacRevokeBusyKey, setRbacRevokeBusyKey] = useState("");
  const [rbacRoles, setRbacRoles] = useState<RbacRoleEntry[]>([]);
  const [rbacAssignments, setRbacAssignments] = useState<RbacAssignmentEntry[]>([]);
  const [newRoleName, setNewRoleName] = useState("");
  const [newRolePermissions, setNewRolePermissions] = useState("admin.dashboard.read");
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRoleName, setAssignRoleName] = useState("");
  const [assignmentUserFilter, setAssignmentUserFilter] = useState("");
  const [assignmentRoleFilter, setAssignmentRoleFilter] = useState("");

  const rbacFilterBadges = useMemo(
    () => [
      assignmentUserFilter.trim() ? `${tx("rbacFilterUser")}: ${assignmentUserFilter.trim()}` : "",
      assignmentRoleFilter.trim() ? `${tx("rbacFilterRole")}: ${assignmentRoleFilter.trim()}` : "",
    ].filter(Boolean),
    [assignmentRoleFilter, assignmentUserFilter, tx],
  );

  const rbacAssignmentRows = useMemo(
    () => rbacAssignments.flatMap((row) => row.roles.map((role) => ({ user_id: row.user_id, role }))),
    [rbacAssignments],
  );

  const loadRbacRoles = useCallback(async () => {
    setRbacRolesBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/rbac/roles`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { roles?: Record<string, string[]> };
      const rows = Object.entries(json.roles || {}).map(([name, permissions]) => ({
        name,
        permissions: permissions || [],
      }));
      setRbacRoles(rows);
      setAssignRoleName((current) => current || rows[0]?.name || "");
      setRbacFeedback(null);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRolesBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  const loadRbacAssignments = useCallback(async () => {
    setRbacAssignmentsBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const params = new URLSearchParams();
      if (assignmentUserFilter.trim()) {
        params.set("user_id", assignmentUserFilter.trim());
      }
      if (assignmentRoleFilter.trim()) {
        params.set("role", assignmentRoleFilter.trim());
      }

      const query = params.toString();
      const endpoint = query ? `${baseUrl}/admin/rbac/assignments?${query}` : `${baseUrl}/admin/rbac/assignments`;
      const res = await fetch(endpoint, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { assignments?: RbacAssignmentEntry[] };
      setRbacAssignments(json.assignments || []);
      setRbacFeedback(null);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignmentsBusy(false);
    }
  }, [assignmentRoleFilter, assignmentUserFilter, buildAuthHeaders, l.errorPrefix]);

  const saveRbacRole = useCallback(async () => {
    setRbacFeedback(null);
    if (!newRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacRoleRequired") });
      return;
    }

    setRbacRoleSaveBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/rbac/roles`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          name: newRoleName.trim(),
          permissions: newRolePermissions
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setRbacFeedback({ tone: "success", message: tx("rbacRoleSaved") });
      setNewRoleName("");
      await loadRbacRoles();
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRoleSaveBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix, loadRbacRoles, newRoleName, newRolePermissions, tx]);

  const assignRbacRole = useCallback(async () => {
    setRbacFeedback(null);
    if (!assignUserId.trim() || !assignRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacAssignRequired") });
      return;
    }

    setRbacAssignBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/rbac/assign`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: assignUserId.trim(),
          role: assignRoleName.trim(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      setRbacFeedback({ tone: "success", message: tx("rbacAssigned") });
      await loadRbacAssignments();
      await onAfterMutate?.();
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignBusy(false);
    }
  }, [assignRoleName, assignUserId, buildAuthHeaders, l.errorPrefix, loadRbacAssignments, onAfterMutate, tx]);

  const revokeRbacRole = useCallback(async (userId: string, role: string) => {
    setRbacFeedback(null);
    const revokeLabel = `${userId} / ${role}`;
    const confirmed = window.confirm(tx("rbacRevokeConfirm") + `\n${revokeLabel}`);
    if (!confirmed) {
      setRbacFeedback({ tone: "info", message: tx("rbacRevokeCancelled") });
      return;
    }

    setRbacRevokeBusyKey(`${userId}:${role}`);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(
        `${baseUrl}/admin/rbac/assignments/${encodeURIComponent(userId)}/${encodeURIComponent(role)}`,
        {
          method: "DELETE",
          headers: {
            ...buildAuthHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      await loadRbacAssignments();
      await onAfterMutate?.();
      setRbacFeedback({ tone: "success", message: tx("rbacRevoked") });
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacRevokeBusyKey("");
    }
  }, [buildAuthHeaders, l.errorPrefix, loadRbacAssignments, onAfterMutate, tx]);

  const clearRbacFilters = useCallback(async () => {
    setAssignmentUserFilter("");
    setAssignmentRoleFilter("");
    setRbacFeedback(null);
    setRbacAssignmentsBusy(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/rbac/assignments`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${err.detail || res.status}`,
        });
        return;
      }

      const json = (await res.json()) as { assignments?: RbacAssignmentEntry[] };
      setRbacAssignments(json.assignments || []);
    } catch (error) {
      setRbacFeedback({ tone: "error", message: String(error) });
    } finally {
      setRbacAssignmentsBusy(false);
    }
  }, [buildAuthHeaders, l.errorPrefix]);

  useEffect(() => {
    if (activeTab !== "rbac") {
      return;
    }
    void loadRbacRoles();
    void loadRbacAssignments();
  }, [activeTab, loadRbacAssignments, loadRbacRoles]);

  return {
    rbacFeedback,
    rbacRolesBusy,
    rbacRoleSaveBusy,
    rbacAssignmentsBusy,
    rbacAssignBusy,
    rbacRevokeBusyKey,
    rbacRoles,
    rbacAssignments,
    newRoleName,
    newRolePermissions,
    assignUserId,
    assignRoleName,
    assignmentUserFilter,
    assignmentRoleFilter,
    rbacFilterBadges,
    rbacAssignmentRows,
    setNewRoleName,
    setNewRolePermissions,
    setAssignUserId,
    setAssignRoleName,
    setAssignmentUserFilter,
    setAssignmentRoleFilter,
    loadRbacRoles,
    loadRbacAssignments,
    saveRbacRole,
    assignRbacRole,
    revokeRbacRole,
    clearRbacFilters,
  };
}
