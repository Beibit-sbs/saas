import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminShell } from "../../app/admin/components/AdminShell";

describe("AdminShell", () => {
  const mockSections = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "languages", label: "Languages", icon: "🌐" },
    { id: "users", label: "Local Users", icon: "👥" },
    { id: "rbac", label: "RBAC", icon: "🔐" },
  ];

  it("should render header with platform name", () => {
    render(
      <AdminShell
        activeTab="overview"
        onTabChange={vi.fn()}
        sections={mockSections}
        platformName="Test Platform"
      >
        <div>Content</div>
      </AdminShell>
    );

    expect(screen.getByText("Test Platform")).toBeInTheDocument();
    expect(screen.getByText("Admin Console")).toBeInTheDocument();
  });

  it("should render all sidebar sections", () => {
    render(
      <AdminShell
        activeTab="overview"
        onTabChange={vi.fn()}
        sections={mockSections}
      >
        <div>Content</div>
      </AdminShell>
    );

    mockSections.forEach((section) => {
      expect(screen.getByText(section.label)).toBeInTheDocument();
    });
  });

  it("should highlight active section", () => {
    render(
      <AdminShell
        activeTab="languages"
        onTabChange={vi.fn()}
        sections={mockSections}
      >
        <div>Content</div>
      </AdminShell>
    );

    const languagesButton = screen.getByTestId("sidebar-section-languages");
    expect(languagesButton).toHaveClass("active");
  });

  it("should call onTabChange when section is clicked", async () => {
    const handleTabChange = vi.fn();
    const user = userEvent.setup();

    render(
      <AdminShell
        activeTab="overview"
        onTabChange={handleTabChange}
        sections={mockSections}
      >
        <div>Content</div>
      </AdminShell>
    );

    const usersButton = screen.getByTestId("sidebar-section-users");
    await user.click(usersButton);

    expect(handleTabChange).toHaveBeenCalledWith("users");
  });

  it("should render children content", () => {
    render(
      <AdminShell
        activeTab="overview"
        onTabChange={vi.fn()}
        sections={mockSections}
      >
        <div data-testid="test-content">Custom Content</div>
      </AdminShell>
    );

    expect(screen.getByTestId("test-content")).toBeInTheDocument();
    expect(screen.getByText("Custom Content")).toBeInTheDocument();
  });

  it("should render with default platform name if not provided", () => {
    render(
      <AdminShell
        activeTab="overview"
        onTabChange={vi.fn()}
        sections={mockSections}
      >
        <div>Content</div>
      </AdminShell>
    );

    expect(screen.getByText("Platform")).toBeInTheDocument();
  });
});
