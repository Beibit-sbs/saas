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
  PlatformSectionView: ({ section }: { section: string }) => <div>section:{section}</div>,
}));

describe("PlatformSectionPage routing", () => {
  it("maps known section slug to control-plane tab", () => {
    render(<PlatformSectionPage params={{ section: "tenants" }} />);

    expect(screen.getByText("section:tenants")).toBeInTheDocument();
  });

  it("calls notFound for unknown section slug", () => {
    expect(() => render(<PlatformSectionPage params={{ section: "unknown" }} />)).toThrow("NOT_FOUND");
  });
});
