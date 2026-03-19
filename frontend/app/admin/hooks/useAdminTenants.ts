import { useCallback, useEffect, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { AdminTab, InlineFeedback } from "../types";

export type Tenant = {
  id: number;
  slug: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
};

type UseAdminTenantsParams = {
  activeTab: AdminTab;
  buildAuthHeaders: () => Record<string, string>;
};

type UseAdminTenantsResult = {
  tenants: Tenant[];
  loading: boolean;
  mutating: boolean;
  feedback: InlineFeedback | null;
  lastUpdated: string;
  refresh: () => Promise<void>;
  createTenant: (payload: { slug: string; name: string; status: string }) => Promise<Tenant | null>;
  updateTenant: (id: number, payload: { name?: string; status?: string }) => Promise<Tenant | null>;
  deleteTenant: (id: number) => Promise<boolean>;
};

export function useAdminTenants({
  activeTab,
  buildAuthHeaders,
}: UseAdminTenantsParams): UseAdminTenantsResult {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [mutating, setMutating] = useState(false);
  const [feedback, setFeedback] = useState<InlineFeedback | null>(null);
  const [lastUpdated, setLastUpdated] = useState("-");

  const refresh = useCallback(async () => {
    setLoading(true);
    if (!mutating) {
      setFeedback(null);
    }
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/admin/tenants`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setFeedback({ tone: "error", message: `Error: ${String((err as Record<string, unknown>).detail || res.status)}` });
        return;
      }
      const json = (await res.json()) as { tenants: Tenant[] };
      setTenants(json.tenants || []);
      setLastUpdated(new Date().toLocaleString());
    } catch (error) {
      setFeedback({ tone: "error", message: String(error) });
    } finally {
      setLoading(false);
    }
  }, [buildAuthHeaders, mutating]);

  useEffect(() => {
    if (activeTab === "tenants") {
      refresh();
    }
  }, [activeTab, refresh]);

  const createTenant = useCallback(
    async (payload: { slug: string; name: string; status: string }) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const res = await fetch(`${baseUrl}/admin/tenants`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...buildAuthHeaders(), ...csrfHeaders },
          credentials: "include",
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String((err as Record<string, unknown>).detail || res.status)}` });
          return null;
        }
        const json = (await res.json()) as { tenant: Tenant };
        setFeedback({ tone: "success", message: "Tenant created" });
        await refresh();
        return json.tenant || null;
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
        return null;
      } finally {
        setMutating(false);
      }
    },
    [buildAuthHeaders, refresh],
  );

  const updateTenant = useCallback(
    async (id: number, payload: { name?: string; status?: string }) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const res = await fetch(`${baseUrl}/admin/tenants/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...buildAuthHeaders(), ...csrfHeaders },
          credentials: "include",
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String((err as Record<string, unknown>).detail || res.status)}` });
          return null;
        }
        const json = (await res.json()) as { tenant: Tenant };
        setFeedback({ tone: "success", message: "Tenant updated" });
        await refresh();
        return json.tenant || null;
      } catch (error) {
        setFeedback({ tone: "error", message: String(error) });
        return null;
      } finally {
        setMutating(false);
      }
    },
    [buildAuthHeaders, refresh],
  );

  const deleteTenant = useCallback(
    async (id: number) => {
      setMutating(true);
      setFeedback(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const res = await fetch(`${baseUrl}/admin/tenants/${id}`, {
          method: "DELETE",
          headers: { ...buildAuthHeaders(), ...csrfHeaders },
          credentials: "include",
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setFeedback({ tone: "error", message: `Error: ${String((err as Record<string, unknown>).detail || res.status)}` });
          return false;
        }
        setFeedback({ tone: "success", message: "Tenant deactivated" });
        await refresh();
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

  return { tenants, loading, mutating, feedback, lastUpdated, refresh, createTenant, updateTenant, deleteTenant };
}
