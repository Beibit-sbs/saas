/**
 * Tests for Academic Integrity admin page component.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AcademicIntegrityPage from "@/app/(admin)/console/academic-integrity/page";

vi.mock("@/app/components/LanguageProvider", () => ({
  LanguageProvider: ({ children }: { children: React.ReactNode }) => children,
  useLanguage: () => ({
    language: "ru",
    setLanguage: vi.fn(),
    supportedLanguages: [],
    reloadLanguages: async () => {},
    t: (key: string) => key,
  }),
}));

vi.mock("@/shared/providers/LanguageProvider", () => ({
  LanguageProvider: ({ children }: { children: React.ReactNode }) => children,
  useLanguage: () => ({
    language: "ru",
    setLanguage: vi.fn(),
    supportedLanguages: [],
    reloadLanguages: async () => {},
    t: (key: string) => key,
  }),
}));

// Mock the hooks
vi.mock("@/modules/academic-integrity/hooks", () => ({
  useIntegrityCases: vi.fn(() => ({
    data: {
      cases: [
        {
          id: "case-1",
          student_id: "student-1",
          course_id: "course-1",
          assignment_id: null,
          case_type: "plagiarism",
          description: "High similarity detected in submission",
          evidence_url: "https://example.com/report",
          priority: "high",
          status: "flagged",
          resolution_notes: null,
          recommended_action: null,
          created_at: "2026-04-21T10:00:00Z",
          updated_at: "2026-04-21T10:00:00Z",
          created_by: "admin@example.com",
          tenant_id: "test-tenant",
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    },
    isLoading: false,
    error: null,
  })),
  useCreateIntegrityCase: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useUpdateIntegrityCaseStatus: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
}));

function renderWithProviders(component: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
}

describe("AcademicIntegrityPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page with title", () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    // Should render Russian and English titles
    const titleText = screen.queryByText(/Академическая честность|Academic Integrity/);
    expect(titleText).toBeTruthy();
  });

  it("renders cases table with data", () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    // Check for student ID in table
    expect(screen.getByText("student-1")).toBeTruthy();
    // Check for course ID
    expect(screen.getByText("course-1")).toBeTruthy();
  });

  it("renders Create Case button", () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    const createButton = screen.queryByText(/Создать дело|Create Case/);
    expect(createButton).toBeTruthy();
  });

  it("opens create dialog when button is clicked", async () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    const createButton = screen.queryByText(/Создать дело|Create Case/);
    if (createButton) {
      fireEvent.click(createButton);
      
      // Check if dialog content appears
      await waitFor(() => {
        const dialogTitle = screen.queryByText(/Новое дело|New Integrity Case/);
        expect(dialogTitle).toBeTruthy();
      });
    }
  });

  it("displays case status badge", () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    // Look for status badge (flagged case should show)
    const statusBadge = screen.queryByText(/Отмечено|Flagged/);
    expect(statusBadge).toBeTruthy();
  });

  it("renders filter input for status", () => {
    renderWithProviders(<AcademicIntegrityPage />);
    
    const filterInput = screen.getByPlaceholderText(/Фильтр по статусу|Filter by status/);
    expect(filterInput).toBeTruthy();
  });
});
