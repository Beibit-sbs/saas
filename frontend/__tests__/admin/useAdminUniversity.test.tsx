import { describe, expect, it, beforeEach, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { useAdminUniversity } from "../../app/admin/hooks/useAdminUniversity";

vi.mock("../../app/components/csrf", () => ({
  buildCsrfHeaders: vi.fn(async () => ({ "x-csrf-token": "test" })),
}));

describe("useAdminUniversity", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("loads list data when tab is active", async () => {
    const buildAuthHeaders = vi.fn(() => ({ Authorization: "Bearer token" }));
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          students: [
            {
              id: 1,
              student_id: "ST-1",
              first_name: "Ainur",
              last_name: "Sarsen",
              email: "ainur@example.edu",
              status: "active",
              tenant_id: null,
              created_at: "2026-03-20T00:00:00Z",
            },
          ],
        }),
        { status: 200 },
      ),
    );

    const { result } = renderHook(() =>
      useAdminUniversity({
        activeTab: "university",
        buildAuthHeaders,
      }),
    );

    await waitFor(() => {
      expect(result.current.itemsByEntity.students).toHaveLength(1);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bff/admin/university/students",
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
      }),
    );
  });

  it("sets error feedback on list load failure", async () => {
    const buildAuthHeaders = vi.fn(() => ({}));
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "forbidden" }), { status: 403 }),
    );

    const { result } = renderHook(() =>
      useAdminUniversity({
        activeTab: "university",
        buildAuthHeaders,
      }),
    );

    await waitFor(() => {
      expect(result.current.feedback?.tone).toBe("error");
      expect(result.current.feedback?.message).toContain("forbidden");
    });
  });

  it("runs create, update, delete requests for representative entity", async () => {
    const buildAuthHeaders = vi.fn(() => ({ Authorization: "Bearer token" }));
    const fetchMock = vi.mocked(fetch);

    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ student: { id: 11 } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ students: [{ id: 11, student_id: "ST-11" }] }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ student: { id: 11 } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ students: [{ id: 11, student_id: "ST-11" }] }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ deleted: true }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ students: [] }), { status: 200 }),
      );

    const { result } = renderHook(() =>
      useAdminUniversity({
        activeTab: "overview",
        buildAuthHeaders,
      }),
    );

    const payload = {
      student_id: "ST-11",
      first_name: "Alina",
      last_name: "Bek",
      email: "alina@example.edu",
      status: "active",
      tenant_id: null,
    };

    let created: Record<string, unknown> | null = null;
    await act(async () => {
      created = await result.current.createItem("students", payload);
    });
    expect(created).toEqual({ id: 11 });

    let updated: Record<string, unknown> | null = null;
    await act(async () => {
      updated = await result.current.updateItem("students", 11, { ...payload, status: "on_leave" });
    });
    expect(updated).toEqual({ id: 11 });

    let deleted = false;
    await act(async () => {
      deleted = await result.current.deleteItem("students", 11);
    });
    expect(deleted).toBe(true);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(6);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bff/admin/university/students",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bff/admin/university/students/11",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bff/admin/university/students/11",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});
