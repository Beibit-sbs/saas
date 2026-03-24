// Shared API types used across all modules

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface ApiError {
  status: number;
  detail: string;
  code?: string;
}

export interface RequestConfig {
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

export type SortDir = "asc" | "desc";

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface FilterParams {
  search?: string;
  status?: string;
  [key: string]: string | number | boolean | undefined;
}
