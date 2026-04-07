"use client";

import { useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

interface DetailDrawerOptions {
  paramKey?: string;
}

export function useDetailDrawer({ paramKey = "detail" }: DetailDrawerOptions = {}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedId = searchParams.get(paramKey);

  const update = useCallback(
    (nextId: string | null) => {
      const next = new URLSearchParams(searchParams.toString());
      if (nextId) {
        next.set(paramKey, nextId);
      } else {
        next.delete(paramKey);
      }
      const query = next.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [paramKey, pathname, router, searchParams],
  );

  return {
    isOpen: !!selectedId,
    selectedId,
    open: (id: string) => update(id),
    close: () => update(null),
  };
}