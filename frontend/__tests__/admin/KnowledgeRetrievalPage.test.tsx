import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import KnowledgeRetrievalPage from "../../app/(admin)/console/knowledge-retrieval/page";

let allowAccess = true;

vi.mock("../../modules/knowledge-retrieval/hooks", () => ({
  useIngestDocument: () => ({ mutate: vi.fn(), isPending: false, data: null }),
  useSemanticSearch: () => ({ mutate: vi.fn(), isPending: false, data: null }),
  useKnowledgeBaseStats: () => ({
    data: { total_documents: 3, total_chunks: 12, doc_type_breakdown: { policy: 3 } },
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

describe("KnowledgeRetrievalPage", () => {
  beforeEach(() => {
    allowAccess = true;
  });

  it("renders page title", () => {
    render(<KnowledgeRetrievalPage />);
    expect(screen.getByText(/Knowledge Retrieval/i)).toBeInTheDocument();
  });

  it("renders stats panel", () => {
    render(<KnowledgeRetrievalPage />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Documents")).toBeInTheDocument();
  });

  it("renders ingest form", () => {
    render(<KnowledgeRetrievalPage />);
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<KnowledgeRetrievalPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
