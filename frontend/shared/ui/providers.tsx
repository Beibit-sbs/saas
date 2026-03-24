"use client";

import { ReactNode, useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AdminAuthProvider } from "@/shared/auth/context";
import { BACKEND_UNAVAILABLE_EVENT } from "@/shared/auth/session-events";
import { Toaster } from "@/shared/ui/toaster";
import { toast } from "@/shared/ui/use-toast";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 1,
          },
        },
      }),
  );

  useEffect(() => {
    let lastShownAt = 0;
    const handler = () => {
      const now = Date.now();
      if (now - lastShownAt < 5000) return;
      lastShownAt = now;
      toast({
        variant: "destructive",
        title: "Backend unavailable",
        description: "The admin API is temporarily unavailable. Retry in a moment.",
      });
    };

    window.addEventListener(BACKEND_UNAVAILABLE_EVENT, handler);
    return () => window.removeEventListener(BACKEND_UNAVAILABLE_EVENT, handler);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AdminAuthProvider>
        {children}
        <Toaster />
      </AdminAuthProvider>
    </QueryClientProvider>
  );
}
