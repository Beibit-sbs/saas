"use client";

import { useCallback } from "react";
import { useToast } from "@/shared/ui/use-toast";
import { normalizeApiError } from "@/shared/utils/api-error";

interface FeedbackOptions<TResult> {
  successTitle: string | ((result: TResult) => string);
  successDescription?: string | ((result: TResult) => string | undefined);
  errorTitle?: string;
}

export function useMutationFeedback() {
  const { toast } = useToast();

  const getHandlers = useCallback(
    <TResult = unknown>({ successTitle, successDescription, errorTitle }: FeedbackOptions<TResult>) => ({
      onSuccess: (result: TResult) => {
        toast({
          variant: "success",
          title: typeof successTitle === "function" ? successTitle(result) : successTitle,
          description:
            typeof successDescription === "function" ? successDescription(result) : successDescription,
        });
      },
      onError: (error: unknown) => {
        const normalized = normalizeApiError(error);
        toast({
          variant: "destructive",
          title: errorTitle ?? normalized.message,
          description: normalized.actionable || undefined,
        });
      },
    }),
    [toast],
  );

  return { getHandlers };
}