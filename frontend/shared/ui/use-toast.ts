"use client";

import { useCallback } from "react";
import { toast as toasterToast } from "./toaster";

type ToastInput = Parameters<typeof toasterToast>[0];

/**
 * Thin hook that delegates to the single global toast store in toaster.tsx.
 * Using this hook (or the exported `toast`) guarantees the <Toaster> component
 * will display the notification.
 */
export function useToast() {
  const toast = useCallback((props: ToastInput) => {
    toasterToast(props);
  }, []);

  return { toast };
}

export const toast = toasterToast;
