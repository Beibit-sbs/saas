"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export type SortDirection = "asc" | "desc";

export interface TableSortState {
  key: string;
  direction: SortDirection;
}

interface TableQueryStateOptions<TFilterKey extends string> {
  filterKeys: readonly TFilterKey[];
  defaultPageSize?: number;
  defaultSort?: TableSortState | null;
}

function parsePositiveInteger(value: string | null, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export function useTableQueryState<TFilterKey extends string>({
  filterKeys,
  defaultPageSize = 20,
  defaultSort = null,
}: TableQueryStateOptions<TFilterKey>) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const page = parsePositiveInteger(searchParams.get("page"), 1);
  const pageSize = parsePositiveInteger(searchParams.get("pageSize"), defaultPageSize);
  const sort = useMemo<TableSortState | null>(() => {
    const raw = searchParams.get("sort");
    if (!raw) return defaultSort;
    const [key, direction] = raw.split(":");
    if (!key || (direction !== "asc" && direction !== "desc")) return defaultSort;
    return { key, direction };
  }, [defaultSort, searchParams]);

  const filters = useMemo(
    () =>
      filterKeys.reduce(
        (acc, key) => {
          acc[key] = searchParams.get(key) ?? "";
          return acc;
        },
        {} as Record<TFilterKey, string>,
      ),
    [filterKeys, searchParams],
  );

  const replaceParams = useCallback(
    (mutate: (params: URLSearchParams) => void) => {
      const next = new URLSearchParams(searchParams.toString());
      mutate(next);

      if (next.get("page") === "1") next.delete("page");
      if (next.get("pageSize") === String(defaultPageSize)) next.delete("pageSize");
      if (defaultSort && next.get("sort") === `${defaultSort.key}:${defaultSort.direction}`) next.delete("sort");

      const query = next.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [defaultPageSize, defaultSort, pathname, router, searchParams],
  );

  const setPage = useCallback(
    (nextPage: number) => {
      replaceParams((params) => {
        params.set("page", String(Math.max(1, nextPage)));
      });
    },
    [replaceParams],
  );

  const setPageSize = useCallback(
    (nextPageSize: number) => {
      replaceParams((params) => {
        params.set("pageSize", String(nextPageSize));
        params.set("page", "1");
      });
    },
    [replaceParams],
  );

  const setFilter = useCallback(
    (key: string, value: string) => {
      replaceParams((params) => {
        if (value) {
          params.set(key, value);
        } else {
          params.delete(key);
        }
        params.set("page", "1");
      });
    },
    [replaceParams],
  );

  const resetFilters = useCallback(() => {
    replaceParams((params) => {
      filterKeys.forEach((key) => params.delete(key));
      params.delete("sort");
      params.set("page", "1");
    });
  }, [filterKeys, replaceParams]);

  const setSort = useCallback(
    (key: string) => {
      replaceParams((params) => {
        const current = sort?.key === key ? sort.direction : null;
        if (current === "asc") {
          params.set("sort", `${key}:desc`);
        } else if (current === "desc") {
          params.delete("sort");
        } else {
          params.set("sort", `${key}:asc`);
        }
        params.set("page", "1");
      });
    },
    [replaceParams, sort],
  );

  return {
    filters,
    page,
    pageSize,
    setFilter,
    resetFilters,
    setPage,
    setPageSize,
    setSort,
    sort,
  };
}