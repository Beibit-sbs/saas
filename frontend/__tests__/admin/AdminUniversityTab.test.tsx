import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AdminUniversityTab } from "../../app/admin/components/AdminUniversityTab";
import type { UniversityEntity } from "../../app/admin/hooks/useAdminUniversity";

const emptyItems = {
  students: [],
  faculty: [],
  programs: [],
  courses: [],
  enrollments: [],
  records: [],
};

describe("AdminUniversityTab", () => {
  const realConsoleError = console.error;
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation((...args) => {
      const firstArg = String(args[0] ?? "");
      if (firstArg.includes("not wrapped in act(...)") || firstArg.includes("wrap-tests-with-act")) {
        return;
      }
      realConsoleError(...args);
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renders University tab base UI", () => {
    render(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={vi.fn()}
        itemsByEntity={emptyItems}
        loading={false}
        mutating={false}
        feedback={null}
        lastUpdated="2026-03-20 10:00"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={vi.fn(async () => null)}
        onUpdateItem={vi.fn(async () => null)}
        onDeleteItem={vi.fn(async () => false)}
      />,
    );

    expect(screen.getByText("University Core")).toBeInTheDocument();
    expect(screen.getByText("Students CRUD")).toBeInTheDocument();
    expect(screen.getByText("Students Table")).toBeInTheDocument();
    expect(screen.getByText("Rows: 0")).toBeInTheDocument();
    expect(screen.getByText("Mode: Create")).toBeInTheDocument();
  });

  it("renders all university sub-sections and switches via callback", async () => {
    const user = userEvent.setup();
    const onEntityChange = vi.fn();

    render(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={onEntityChange}
        itemsByEntity={emptyItems}
        loading={false}
        mutating={false}
        feedback={null}
        lastUpdated="-"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={vi.fn(async () => null)}
        onUpdateItem={vi.fn(async () => null)}
        onDeleteItem={vi.fn(async () => false)}
      />,
    );

    const sections: Array<{ label: string; entity: UniversityEntity }> = [
      { label: "Students", entity: "students" },
      { label: "Faculty", entity: "faculty" },
      { label: "Programs", entity: "programs" },
      { label: "Courses", entity: "courses" },
      { label: "Enrollments", entity: "enrollments" },
      { label: "Records", entity: "records" },
    ];

    for (const section of sections) {
      const button = screen.getByRole("button", { name: section.label });
      expect(button).toBeInTheDocument();
      await user.click(button);
      expect(onEntityChange).toHaveBeenCalledWith(section.entity);
    }
  });

  it("renders list rows for active entity", () => {
    render(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={vi.fn()}
        itemsByEntity={{
          ...emptyItems,
          students: [
            {
              id: 10,
              student_id: "ST-10",
              first_name: "Dana",
              last_name: "Kim",
              email: "dana.kim@example.edu",
              status: "active",
              tenant_id: null,
              created_at: "2026-03-20T00:00:00Z",
            },
          ],
        }}
        loading={false}
        mutating={false}
        feedback={null}
        lastUpdated="-"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={vi.fn(async () => null)}
        onUpdateItem={vi.fn(async () => null)}
        onDeleteItem={vi.fn(async () => false)}
      />,
    );

    expect(screen.getByText("Rows: 1")).toBeInTheDocument();
    expect(screen.getByText("ST-10")).toBeInTheDocument();
    expect(screen.getByText("Dana")).toBeInTheDocument();
  });

  it("covers create, update and delete interactions for students", async () => {
    const user = userEvent.setup();
    const onCreateItem = vi.fn(async () => ({ id: 2 }));
    const onUpdateItem = vi.fn(async () => ({ id: 1 }));
    const onDeleteItem = vi.fn(async () => true);

    render(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={vi.fn()}
        itemsByEntity={{
          ...emptyItems,
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
        }}
        loading={false}
        mutating={false}
        feedback={null}
        lastUpdated="-"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={onCreateItem}
        onUpdateItem={onUpdateItem}
        onDeleteItem={onDeleteItem}
      />,
    );

    await user.type(screen.getByPlaceholderText("Student ID"), "ST-2");
    await user.type(screen.getByPlaceholderText("First name"), "Alina");
    await user.type(screen.getByPlaceholderText("Last name"), "Bek");
    await user.type(screen.getByPlaceholderText("Email"), "alina@example.edu");
    await user.type(screen.getByPlaceholderText("Status"), "active");

    await act(async () => {
      await user.click(screen.getByRole("button", { name: "Create student" }));
    });
    await waitFor(() => {
      expect(onCreateItem).toHaveBeenCalledTimes(1);
      expect(onCreateItem).toHaveBeenCalledWith("students", {
        student_id: "ST-2",
        first_name: "Alina",
        last_name: "Bek",
        email: "alina@example.edu",
        status: "active",
        tenant_id: null,
      });
    });

    await act(async () => {
      await user.click(screen.getByRole("button", { name: "Edit" }));
    });
    expect(screen.getByText("Mode: Update")).toBeInTheDocument();

    const statusInput = screen.getByDisplayValue("active");
    await user.clear(statusInput);
    await user.type(statusInput, "on_leave");

    await act(async () => {
      await user.click(screen.getByRole("button", { name: "Update student" }));
    });
    await waitFor(() => {
      expect(onUpdateItem).toHaveBeenCalledTimes(1);
      expect(onUpdateItem).toHaveBeenCalledWith("students", 1, {
        student_id: "ST-1",
        first_name: "Ainur",
        last_name: "Sarsen",
        email: "ainur@example.edu",
        status: "on_leave",
        tenant_id: null,
      });
    });

    const deleteButton = screen.getByRole("button", { name: "Delete" });
    await act(async () => {
      await user.click(deleteButton);
    });

    await waitFor(() => {
      expect(onDeleteItem).toHaveBeenCalledTimes(1);
      expect(onDeleteItem).toHaveBeenCalledWith("students", 1);
    });
  });

  it("renders success and error feedback", () => {
    const { rerender } = render(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={vi.fn()}
        itemsByEntity={emptyItems}
        loading={false}
        mutating={false}
        feedback={{ tone: "success", message: "Created successfully" }}
        lastUpdated="-"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={vi.fn(async () => null)}
        onUpdateItem={vi.fn(async () => null)}
        onDeleteItem={vi.fn(async () => false)}
      />,
    );

    expect(screen.getByText("Created successfully")).toBeInTheDocument();

    rerender(
      <AdminUniversityTab
        activeEntity="students"
        onEntityChange={vi.fn()}
        itemsByEntity={emptyItems}
        loading={false}
        mutating={false}
        feedback={{ tone: "error", message: "Error: 500" }}
        lastUpdated="-"
        onRefresh={vi.fn(async () => undefined)}
        onCreateItem={vi.fn(async () => null)}
        onUpdateItem={vi.fn(async () => null)}
        onDeleteItem={vi.fn(async () => false)}
      />,
    );

    expect(screen.getByText("Error: 500")).toBeInTheDocument();
  });
});
