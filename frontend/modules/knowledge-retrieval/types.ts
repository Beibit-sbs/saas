export interface IngestDocumentPayload {
  title: string;
  content: string;
  doc_type?: "policy" | "guideline" | "syllabus" | "research" | "general";
  source_ref?: string;
  tags?: string[];
}

export interface IngestDocumentResponse {
  doc_id: string;
  title: string;
  doc_type: string;
  status: string;
  chunk_count: number;
}

export interface SemanticSearchPayload {
  query: string;
  doc_type?: "policy" | "guideline" | "syllabus" | "research" | "general";
  top_k?: number;
}

export interface SearchResultItem {
  doc_id: string;
  title: string;
  doc_type: string;
  excerpt: string;
  score: number;
  source_ref: string | null;
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchResultItem[];
  total_found: number;
}

export interface KnowledgeBaseStats {
  total_documents: number;
  total_chunks: number;
  doc_type_breakdown: Record<string, number>;
  last_ingest_at: string | null;
}
