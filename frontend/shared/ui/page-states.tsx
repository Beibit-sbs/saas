import { Loader2 } from "lucide-react";

import { ErrorState as BaseErrorState } from "./error-state";

interface LoadingStateProps {
  title?: string;
  message?: string;
}

interface PageErrorStateProps {
  error?: unknown;
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  retrying?: boolean;
}

function getErrorMessage(error: unknown): string | undefined {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }
  if (typeof error === "string" && error.trim().length > 0) {
    return error;
  }
  return undefined;
}

export function LoadingState({
  title = "Loading",
  message = "Fetching the latest data for this page.",
}: LoadingStateProps) {
  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed px-6 py-12 text-center">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      <div className="space-y-1">
        <h2 className="text-base font-medium text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}

export function ErrorState({
  error,
  title = "Unable to load this page",
  message,
  onRetry,
  retryLabel,
  retrying,
}: PageErrorStateProps) {
  return (
    <BaseErrorState
      title={title}
      message={message ?? getErrorMessage(error) ?? "Try refreshing the page or retry the request."}
      onRetry={onRetry}
      retryLabel={retryLabel}
      retrying={retrying}
    />
  );
}