import type React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppTopbar } from "../../shared/ui/app-topbar";

const useAdminAuthMock = vi.fn();
const useLanguageMock = vi.fn();
const loadLoginTenantDirectoryMock = vi.fn();
const findTenantByIdMock = vi.fn();

vi.mock("../../shared/auth/hooks", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: (...args: unknown[]) => useLanguageMock(...args),
}));

vi.mock("../../app/components/LanguageSwitcher", () => ({
  default: () => <div data-testid="language-switcher" />,
}));

vi.mock("../../app/login/tenant-directory", () => ({
  loadLoginTenantDirectory: (...args: unknown[]) => loadLoginTenantDirectoryMock(...args),
  findTenantById: (...args: unknown[]) => findTenantByIdMock(...args),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("../../shared/ui/dropdown-menu", async () => {
  const React = await import("react");

  type ClickableChildProps = {
    onClick?: (event: React.MouseEvent) => void | Promise<void>;
    className?: string;
    role?: string;
  };

  type DropdownMenuContextValue = {
    open: boolean;
    setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  };

  const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(null);

  function useDropdownMenuContext() {
    const context = React.useContext(DropdownMenuContext);
    if (!context) {
      throw new Error("Dropdown menu mock used outside provider");
    }
    return context;
  }

  function DropdownMenu({ children }: { children: React.ReactNode }) {
    const [open, setOpen] = React.useState(false);
    return <DropdownMenuContext.Provider value={{ open, setOpen }}>{children}</DropdownMenuContext.Provider>;
  }

  function DropdownMenuTrigger({ children, asChild }: { children: React.ReactElement; asChild?: boolean }) {
    const { open, setOpen } = useDropdownMenuContext();
    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<ClickableChildProps>;
      return React.cloneElement(child, {
        onClick: async (event: React.MouseEvent) => {
          await child.props.onClick?.(event);
          setOpen(!open);
        },
      });
    }
    return <button onClick={() => setOpen(!open)}>{children}</button>;
  }

  function DropdownMenuContent({ children }: { children: React.ReactNode }) {
    const { open } = useDropdownMenuContext();
    if (!open) {
      return null;
    }
    return <div role="menu">{children}</div>;
  }

  function DropdownMenuItem({ children, asChild, onSelect, className }: { children: React.ReactElement | React.ReactNode; asChild?: boolean; onSelect?: () => void; className?: string }) {
    const { setOpen } = useDropdownMenuContext();

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<ClickableChildProps>;
      return React.cloneElement(child, {
        role: "menuitem",
        className,
        onClick: async (event: React.MouseEvent) => {
          await child.props.onClick?.(event);
          onSelect?.();
          setOpen(false);
        },
      });
    }

    return (
      <button
        role="menuitem"
        className={className}
        onClick={() => {
          onSelect?.();
          setOpen(false);
        }}
      >
        {children}
      </button>
    );
  }

  function DropdownMenuSeparator() {
    return <hr />;
  }

  return {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
  };
});

describe("AppTopbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLanguageMock.mockReturnValue({
      t: (key: string) => {
        const dict: Record<string, string> = {
          "ui.profile": "Profile",
          "ui.preferences": "Preferences",
          "ui.security": "Security",
          "ui.signOut": "Sign out",
          "ui.platformContext": "Platform Scope",
          "ui.universityIdFallback": "University ID {id}",
        };
        return dict[key] ?? key;
      },
    });
    loadLoginTenantDirectoryMock.mockResolvedValue({ state: "ready", tenants: [] });
    findTenantByIdMock.mockReturnValue(null);
  });

  async function clickWithAct(user: ReturnType<typeof userEvent.setup>, element: Element) {
    await act(async () => {
      await user.click(element);
    });
  }

  it("renders user identity trigger", async () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
        tenantId: 7,
        roles: ["admin"],
      },
      logout: vi.fn(),
    });

    findTenantByIdMock.mockReturnValue({ tenantId: "7", name: "Northwind University" });

    render(<AppTopbar />);

    expect(screen.getByTestId("language-switcher")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /alice admin/i })).toBeInTheDocument();
    expect(screen.getByText("AA")).toBeInTheDocument();
    expect(await screen.findByText("Northwind University")).toBeInTheDocument();
  });

  it("shows safe university ID fallback when name is unavailable", async () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
        tenantId: 12,
        roles: ["admin"],
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    expect(await screen.findByText("University ID 12")).toBeInTheDocument();
  });

  it("shows platform context for superadmin without tenant scope", () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Platform Admin",
        sub: "root",
        roles: ["superadmin"],
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    expect(screen.getByText("Platform Scope")).toBeInTheDocument();
  });

  it("shows profile, preferences and security links in dropdown", async () => {
    const user = userEvent.setup();

    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    await clickWithAct(user, screen.getByRole("button", { name: /alice admin/i }));

    expect(screen.getByRole("menuitem", { name: "Profile" })).toHaveAttribute("href", "/console/profile");
    expect(screen.getByRole("menuitem", { name: "Preferences" })).toHaveAttribute("href", "/console/preferences");
    expect(screen.getByRole("menuitem", { name: "Security" })).toHaveAttribute("href", "/console/security");
  });

  it("calls logout from dropdown action", async () => {
    const user = userEvent.setup();
    const logout = vi.fn();

    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
      },
      logout,
    });

    render(<AppTopbar />);

    await clickWithAct(user, screen.getByRole("button", { name: /alice admin/i }));
    await clickWithAct(user, screen.getByRole("menuitem", { name: "Sign out" }));

    expect(logout).toHaveBeenCalledTimes(1);
  });
});
