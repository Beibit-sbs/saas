import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminCopy, InlineFeedback, RbacAssignmentEntry, RbacRoleEntry, TxFn } from "../types";

const RBAC_BFF_BASE = "/api/bff/admin/rbac";

function rbacBffPath(path: string): string {
  return `${RBAC_BFF_BASE}/${path}`;
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

type UseAdminRbacParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  l: AdminCopy;
  tx: TxFn;
  tenantId?: number | null;
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
  tenantId,
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

  const buildRbacHeaders = useCallback((): Record<string, string> => {
    const headers = buildAuthHeaders();
    if (tenantId && tenantId > 0) {
      return { ...headers, "X-Tenant-ID": String(tenantId) };
    }
    return headers;
  }, [buildAuthHeaders, tenantId]);

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
      const params = new URLSearchParams();
      if (tenantId && tenantId > 0) {
        params.set("tenant_id", String(tenantId));
      }
      const endpoint = params.toString() ? `${rbacBffPath("roles")}?${params.toString()}` : rbacBffPath("roles");
      const res = await fetch(endpoint, {
        headers: buildRbacHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [buildRbacHeaders, l.errorPrefix, tenantId]);

  const loadRbacAssignments = useCallback(async () => {
    setRbacAssignmentsBusy(true);
    try {
      const params = new URLSearchParams();
      if (assignmentUserFilter.trim()) {
        params.set("user_id", assignmentUserFilter.trim());
      }
      if (assignmentRoleFilter.trim()) {
        params.set("role", assignmentRoleFilter.trim());
      }
      if (tenantId && tenantId > 0) {
        params.set("tenant_id", String(tenantId));
      }

      const query = params.toString();
      const endpoint = query ? `${rbacBffPath("assignments")}?${query}` : rbacBffPath("assignments");
      const res = await fetch(endpoint, {
        headers: buildRbacHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [assignmentRoleFilter, assignmentUserFilter, buildRbacHeaders, l.errorPrefix, tenantId]);

  const saveRbacRole = useCallback(async () => {
    setRbacFeedback(null);
    if (!newRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacRoleRequired") });
      return;
    }

    setRbacRoleSaveBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(rbacBffPath("roles"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...buildRbacHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          name: newRoleName.trim(),
          tenant_id: tenantId && tenantId > 0 ? tenantId : undefined,
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
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [buildAuthHeaders, buildRbacHeaders, l.errorPrefix, loadRbacRoles, newRoleName, newRolePermissions, tenantId, tx]);

  const assignRbacRole = useCallback(async () => {
    setRbacFeedback(null);
    if (!assignUserId.trim() || !assignRoleName.trim()) {
      setRbacFeedback({ tone: "error", message: tx("rbacAssignRequired") });
      return;
    }

    setRbacAssignBusy(true);
    try {
      const csrfHeaders = await buildCsrfHeaders("/api");
      const res = await fetch(rbacBffPath("assign"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...buildRbacHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: assignUserId.trim(),
          role: assignRoleName.trim(),
          tenant_id: tenantId && tenantId > 0 ? tenantId : undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [assignRoleName, assignUserId, buildAuthHeaders, buildRbacHeaders, l.errorPrefix, loadRbacAssignments, onAfterMutate, tenantId, tx]);

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
      const csrfHeaders = await buildCsrfHeaders("/api");
      const params = new URLSearchParams();
      if (tenantId && tenantId > 0) {
        params.set("tenant_id", String(tenantId));
      }
      const endpoint = `${rbacBffPath(`assignments/${encodeURIComponent(userId)}/${encodeURIComponent(role)}`)}${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await fetch(
        endpoint,
        {
          method: "DELETE",
          headers: {
            ...buildRbacHeaders(),
            ...csrfHeaders,
          },
          credentials: "include",
        },
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [buildRbacHeaders, l.errorPrefix, loadRbacAssignments, onAfterMutate, tenantId, tx]);

  const clearRbacFilters = useCallback(async () => {
    setAssignmentUserFilter("");
    setAssignmentRoleFilter("");
    setRbacFeedback(null);
    setRbacAssignmentsBusy(true);
    try {
      const params = new URLSearchParams();
      if (tenantId && tenantId > 0) {
        params.set("tenant_id", String(tenantId));
      }
      const endpoint = params.toString() ? `${rbacBffPath("assignments")}?${params.toString()}` : rbacBffPath("assignments");
      const res = await fetch(endpoint, {
        headers: buildRbacHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setRbacFeedback({
          tone: "error",
          message: `${l.errorPrefix}: ${extractErrorDetail(err, res.status)}`,
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
  }, [buildRbacHeaders, l.errorPrefix, tenantId]);

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
