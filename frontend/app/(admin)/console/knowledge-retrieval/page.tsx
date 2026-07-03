"use client";

import { useState } from "react";
import { Database } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useIngestDocument,
  useKnowledgeBaseStats,
  useSemanticSearch,
} from "@/modules/knowledge-retrieval/hooks";

export default function KnowledgeRetrievalPage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [query, setQuery] = useState("");

  const ingest = useIngestDocument();
  const search = useSemanticSearch();
  const { data: stats } = useKnowledgeBaseStats();

  return (
    <RequirePermission permission={PERMISSIONS.KNOWLEDGE_RETRIEVAL_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Knowledge Retrieval"
          description="RAG pipeline — ingest documents and run semantic search across the knowledge base"
          icon={Database}
        />

        {stats && (
          <div className="rounded-lg border bg-card p-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{stats.total_documents}</p>
              <p className="text-sm text-muted-foreground">Documents</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total_chunks}</p>
              <p className="text-sm text-muted-foreground">Chunks</p>
            </div>
            <div>
              <p className="text-2xl font-bold">
                {Object.keys(stats.doc_type_breakdown).length}
              </p>
              <p className="text-sm text-muted-foreground">Doc Types</p>
            </div>
          </div>
        )}

        <RequirePermission permission={PERMISSIONS.KNOWLEDGE_RETRIEVAL_WRITE}>
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <h2 className="text-lg font-semibold">Ingest Document</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="kr_title">Title</Label>
                <Input
                  id="kr_title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Academic Policy 2026"
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="kr_content">Content</Label>
                <Input
                  id="kr_content"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Paste document text here..."
                />
              </div>
            </div>
            <Button
              disabled={ingest.isPending || !title || !content}
              onClick={() => ingest.mutate({ title, content, doc_type: "policy" })}
            >
              {ingest.isPending ? "Ingesting..." : "Ingest Document"}
            </Button>
            {ingest.data && (
              <p className="text-sm text-green-600">
                Indexed: {ingest.data.doc_id} ({ingest.data.chunk_count} chunks)
              </p>
            )}
            {ingest.isError && (
              <p className="text-sm text-destructive">Failed to ingest document. Please try again.</p>
            )}
          </div>
        </RequirePermission>

        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Semantic Search</h2>
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. plagiarism policy"
              className="flex-1"
            />
            <Button
              disabled={search.isPending || !query}
              onClick={() => search.mutate({ query, top_k: 5 })}
            >
              Search
            </Button>
          </div>
          {search.data && (
            <div className="space-y-2">
              {search.data.results.length === 0 ? (
                <p className="text-sm text-muted-foreground">No results found.</p>
              ) : (
                search.data.results.map((r) => (
                  <div key={r.doc_id} className="rounded border p-3 space-y-1">
                    <p className="font-medium text-sm">{r.title}</p>
                    <p className="text-xs text-muted-foreground">{r.excerpt}</p>
                    <p className="text-xs">Score: {r.score}</p>
                  </div>
                ))
              )}
            </div>
          )}
          {search.isError && (
            <p className="text-sm text-destructive">Search failed. Please try again.</p>
          )}
        </div>
      </div>
    </RequirePermission>
  );
}
