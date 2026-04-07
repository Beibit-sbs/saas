import { beforeEach, describe, expect, it, vi } from "vitest";

import { admissionsApi } from "../../../../modules/platform/admissions/api";
import { apiGet, apiPatch, apiPost } from "../../../../shared/api/client";

vi.mock("../../../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
}));

describe("admissionsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls listApplicants with query params", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce({ total: 0, page: 1, page_size: 20, items: [] });

    await admissionsApi.listApplicants({ application_year: 2026, page: 1, page_size: 20 });

    expect(apiGet).toHaveBeenCalledWith("/api/admin/admissions/applicants", {
      application_year: 2026,
      page: 1,
      page_size: 20,
    });
  });

  it("calls createApplicant with payload", async () => {
    vi.mocked(apiPost).mockResolvedValueOnce({ id: 1 });

    await admissionsApi.createApplicant({
      email: "student@example.edu",
      first_name: "Ainur",
      last_name: "Sarsen",
      program_id: 10,
      application_year: 2026,
    });

    expect(apiPost).toHaveBeenCalledWith("/api/admin/admissions/applicants", {
      email: "student@example.edu",
      first_name: "Ainur",
      last_name: "Sarsen",
      program_id: 10,
      application_year: 2026,
    });
  });

  it("calls updateApplicant via PATCH", async () => {
    vi.mocked(apiPatch).mockResolvedValueOnce({ id: 11, first_name: "Alina" });

    await admissionsApi.updateApplicant(11, { first_name: "Alina" });

    expect(apiPatch).toHaveBeenCalledWith("/api/admin/admissions/applicants/11", {
      first_name: "Alina",
    });
  });

  it("uses expected_version when submitting application", async () => {
    vi.mocked(apiPost).mockResolvedValueOnce({ id: 42 });

    await admissionsApi.submitApplication(42, 7);

    expect(apiPost).toHaveBeenCalledWith("/api/admin/admissions/applications/42/submit", {
      expected_version: 7,
    });
  });

  it("loads application documents from documents endpoint", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce({ total: 0, items: [] });

    await admissionsApi.listDocuments(77);

    expect(apiGet).toHaveBeenCalledWith("/api/admin/admissions/applications/77/documents");
  });
});
