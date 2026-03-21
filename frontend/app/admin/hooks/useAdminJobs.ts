import { useCallback, useEffect, useMemo, useState } from "react";

import { buildCsrfHeaders } from "../../components/csrf";
import type { InlineFeedback, JobItem, TxFn } from "../types";

type UseAdminJobsParams = {
  activeTab: string;
  buildAuthHeaders: () => Record<string, string>;
  tx: TxFn;
};

type UseAdminJobsResult = {
  jobs: JobItem[];
  jobsLoading: boolean;
  jobsMutating: boolean;
  jobsFeedback: InlineFeedback | null;
  jobsStatusFilter: string;
  setJobsStatusFilter: (value: string) => void;
  filteredJobs: JobItem[];
  loadJobs: () => Promise<void>;
  createJob: (jobType: string, payload?: Record<string, unknown>) => Promise<void>;
  retryJob: (jobId: number) => Promise<void>;
  cancelJob: (jobId: number) => Promise<void>;
};

export function useAdminJobs({
  activeTab,
  buildAuthHeaders,
  tx,
}: UseAdminJobsParams): UseAdminJobsResult {
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsMutating, setJobsMutating] = useState(false);
  const [jobsFeedback, setJobsFeedback] = useState<InlineFeedback | null>(null);
  const [jobsStatusFilter, setJobsStatusFilter] = useState("");

  const loadJobs = useCallback(async () => {
    setJobsLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const query = jobsStatusFilter.trim() ? `?status=${encodeURIComponent(jobsStatusFilter.trim())}` : "";
      const res = await fetch(`${baseUrl}/admin/jobs${query}`, {
        headers: buildAuthHeaders(),
        credentials: "include",
        cache: "no-store",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setJobsFeedback({ tone: "error", message: `${tx("errorPrefix")}: ${err.detail || res.status}` });
        return;
      }

      const json = (await res.json()) as { jobs?: JobItem[] };
      setJobs(json.jobs || []);
      setJobsFeedback(null);
    } catch (error) {
      setJobsFeedback({ tone: "error", message: String(error) });
    } finally {
      setJobsLoading(false);
    }
  }, [buildAuthHeaders, jobsStatusFilter, tx]);

  const createJob = useCallback(async (jobType: string, payload: Record<string, unknown> = {}) => {
    setJobsMutating(true);
    setJobsFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/jobs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
        body: JSON.stringify({
          job_type: jobType,
          payload,
          max_retries: 3,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setJobsFeedback({ tone: "error", message: `${tx("errorPrefix")}: ${err.detail || res.status}` });
        return;
      }

      setJobsFeedback({ tone: "success", message: "Job queued" });
      await loadJobs();
    } catch (error) {
      setJobsFeedback({ tone: "error", message: String(error) });
    } finally {
      setJobsMutating(false);
    }
  }, [buildAuthHeaders, loadJobs, tx]);

  const retryJob = useCallback(async (jobId: number) => {
    setJobsMutating(true);
    setJobsFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/jobs/${jobId}/retry`, {
        method: "POST",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setJobsFeedback({ tone: "error", message: `${tx("errorPrefix")}: ${err.detail || res.status}` });
        return;
      }

      setJobsFeedback({ tone: "success", message: "Job retried" });
      await loadJobs();
    } catch (error) {
      setJobsFeedback({ tone: "error", message: String(error) });
    } finally {
      setJobsMutating(false);
    }
  }, [buildAuthHeaders, loadJobs, tx]);

  const cancelJob = useCallback(async (jobId: number) => {
    setJobsMutating(true);
    setJobsFeedback(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/admin/jobs/${jobId}/cancel`, {
        method: "POST",
        headers: {
          ...buildAuthHeaders(),
          ...csrfHeaders,
        },
        credentials: "include",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setJobsFeedback({ tone: "error", message: `${tx("errorPrefix")}: ${err.detail || res.status}` });
        return;
      }

      setJobsFeedback({ tone: "success", message: "Job cancelled" });
      await loadJobs();
    } catch (error) {
      setJobsFeedback({ tone: "error", message: String(error) });
    } finally {
      setJobsMutating(false);
    }
  }, [buildAuthHeaders, loadJobs, tx]);

  const filteredJobs = useMemo(() => {
    if (!jobsStatusFilter.trim()) {
      return jobs;
    }
    return jobs.filter((item) => item.status === jobsStatusFilter.trim());
  }, [jobs, jobsStatusFilter]);

  useEffect(() => {
    if (activeTab !== "jobs") {
      return;
    }
    void loadJobs();
  }, [activeTab, loadJobs]);

  return {
    jobs,
    jobsLoading,
    jobsMutating,
    jobsFeedback,
    jobsStatusFilter,
    setJobsStatusFilter,
    filteredJobs,
    loadJobs,
    createJob,
    retryJob,
    cancelJob,
  };
}
