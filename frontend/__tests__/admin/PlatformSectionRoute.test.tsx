import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import PlatformSectionPage from "../../app/(admin)/console/platform/[section]/page";

const notFoundMock = vi.fn(() => {
  throw new Error("NOT_FOUND");
});

vi.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

vi.mock("../../app/(admin)/console/platform/platform-section-view", () => ({
  PlatformSectionView: ({ tab }: { tab: string }) => <div>tab:{tab}</div>,
}));

describe("PlatformSectionPage routing", () => {
  it("maps known section slug to control-plane tab", () => {
    render(<PlatformSectionPage params={{ section: "jobs" }} />);

    expect(screen.getByText("tab:jobs")).toBeInTheDocument();
  });

  it("calls notFound for unknown section slug", () => {
    expect(() => render(<PlatformSectionPage params={{ section: "unknown" }} />)).toThrow("NOT_FOUND");
  });
});
